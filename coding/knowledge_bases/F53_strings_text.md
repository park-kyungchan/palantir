# F53: Strings & Text Processing (문자열과 텍스트 처리)

> **Concept ID**: F53
> **Category**: Data Structures - Strings
> **Difficulty**: Beginner -> Advanced
> **Interview Frequency**: ★★★★★ (Every coding interview)

---

## Section 1: Universal Concept (보편적 개념)

### 1.1 What is a String?

A **String** is a sequence of characters that represents text data. It's one of the most fundamental data types in programming, used everywhere from user input to file processing to network communication.

```
┌─────────────────────────────────────────────────────────────┐
│                     String Mental Model                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   "Hello" in memory (simplified):                           │
│                                                             │
│   Index:   0     1     2     3     4                        │
│          ┌─────┬─────┬─────┬─────┬─────┐                    │
│   Chars: │ 'H' │ 'e' │ 'l' │ 'l' │ 'o' │                    │
│          └─────┴─────┴─────┴─────┴─────┘                    │
│                                                             │
│   String = Character Array + Extra Methods + Metadata       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Immutable vs Mutable Strings

Most modern languages make strings **immutable** - once created, the string's content cannot be changed. This has significant implications:

| Aspect | Immutable (Java, Python, Go) | Mutable (C++ std::string) |
|--------|------------------------------|---------------------------|
| **Thread Safety** | Inherently thread-safe | Requires synchronization |
| **Hashability** | Can be used as dict/map keys | Generally unsafe as keys |
| **Memory** | May waste memory on modifications | More memory-efficient for edits |
| **Performance** | String concatenation is O(n) | In-place modification is O(1) |
| **Interning** | Enables string pooling | Not typically interned |

**Why Immutability?**
1. **Security**: String content can't be altered after validation
2. **Thread Safety**: No locks needed for read access
3. **Caching**: Hash codes can be cached
4. **Memory Optimization**: String interning/pooling

### 1.3 Unicode and Encoding

Understanding character encoding is crucial for string manipulation:

```
┌─────────────────────────────────────────────────────────────┐
│                   Encoding Overview                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ASCII (7-bit): 128 characters (A-Z, a-z, 0-9, symbols)    │
│                                                             │
│   UTF-8:  Variable width (1-4 bytes)                        │
│           - ASCII compatible                                 │
│           - Most common on web/Unix                          │
│           - 'A' = 1 byte, '가' = 3 bytes, '😀' = 4 bytes    │
│                                                             │
│   UTF-16: Variable width (2 or 4 bytes)                     │
│           - Used by Java, JavaScript, Windows               │
│           - BMP chars = 2 bytes, others = 4 bytes (surrogate)│
│           - '가' = 2 bytes, '😀' = 4 bytes                  │
│                                                             │
│   UTF-32: Fixed width (4 bytes per character)               │
│           - Simple indexing but wastes memory               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Concepts:**
- **Code Point**: A number representing a character (e.g., U+0041 = 'A')
- **Code Unit**: The smallest unit of encoding (1 byte in UTF-8, 2 bytes in UTF-16)
- **Grapheme Cluster**: What humans perceive as a single character (e.g., "é" = 'e' + combining accent)

### 1.4 String Interning and Memory Optimization

**String Interning** (or pooling) stores only one copy of each distinct string value:

```
┌─────────────────────────────────────────────────────────────┐
│                   String Pool (Java)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   String a = "hello";  ──┐                                  │
│                          ├──→ Pool: "hello" (single copy)   │
│   String b = "hello";  ──┘                                  │
│                                                             │
│   String c = new String("hello");  ──→ Heap: new "hello"    │
│                                                             │
│   a == b     // true  (same reference from pool)            │
│   a == c     // false (c is on heap, not in pool)           │
│   a.equals(c) // true (content comparison)                  │
│                                                             │
│   c.intern() // Returns reference from pool                 │
│   a == c.intern()  // true                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.5 Why Strings Matter in Interviews

1. **Ubiquitous**: Every program uses strings
2. **Complexity Hidden**: Simple syntax, complex internals
3. **Algorithm Gateway**: Many problems involve string manipulation
4. **Language Mastery**: Shows understanding of memory, Unicode, performance
5. **Real-world Relevance**: Parsing, validation, formatting

---

## Section 2: Semantic Comparison Matrix (의미론적 비교 매트릭스)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Mutability** | Immutable | Immutable | Immutable | Immutable | Immutable | Mutable | Immutable |
| **Internal Encoding** | UTF-16 | UTF-8 (str) | UTF-16 | UTF-8 | Varies (DB) | char/wchar | UTF-8 |
| **Builder Class** | StringBuilder | list.join | array.join | strings.Builder | CONCAT | stringstream | concat() |
| **Interpolation** | No (format) | f"..." | `${...}` | fmt.Sprintf | N/A | std::format (C++20) | N/A |
| **Raw Strings** | Text Block | r"..." | N/A | \`...\` | N/A | R"(...)" | N/A |
| **Length Unit** | char (UTF-16) | char (code point) | UTF-16 code unit | byte | char | char | char |
| **Index Access** | charAt(i) | s[i] | s[i] or charAt | s[i] (byte) | SUBSTRING | s[i] | N/A |
| **Slice** | substring() | s[a:b] | slice() | s[a:b] | SUBSTRING | substr() | substring() |
| **Common Pitfall** | `==` vs `equals()` | Encoding errors | Unicode length | string vs []rune | Collation | null terminator | Column ops |

### 2.2 Detailed Code Examples by Pattern

---

#### Pattern 1: String Creation and Basic Operations

**Java**
```java
// String literals - go to String Pool
String s1 = "Hello";
String s2 = "Hello";
System.out.println(s1 == s2);  // true (same pool reference)

// Constructor - creates new object on heap
String s3 = new String("Hello");
System.out.println(s1 == s3);         // false (different objects)
System.out.println(s1.equals(s3));    // true (same content)

// String interning
String s4 = s3.intern();
System.out.println(s1 == s4);  // true (s4 now points to pool)

// Basic operations
String name = "World";
int length = name.length();           // 5
char first = name.charAt(0);          // 'W'
String upper = name.toUpperCase();    // "WORLD"
String lower = name.toLowerCase();    // "world"
boolean contains = name.contains("or"); // true
int index = name.indexOf("o");        // 1
String sub = name.substring(1, 4);    // "orl"

// Text Blocks (Java 15+) - Multi-line strings
String json = """
    {
        "name": "John",
        "age": 30
    }
    """;

// ⚠️ CRITICAL: Always use equals() for content comparison
String input = scanner.nextLine();
if (input.equals("yes")) { }  // CORRECT
// if (input == "yes") { }    // WRONG - compares references
```

**Python**
```python
# String creation
s1 = "Hello"
s2 = 'Hello'  # Single and double quotes are equivalent
s3 = "Hello"

# Python also interns small strings
print(s1 is s2)  # True (same object, interned)

# But not always for constructed strings
s4 = "Hel" + "lo"
print(s1 is s4)  # True (optimizer may intern)
s5 = "".join(["H", "e", "l", "l", "o"])
print(s1 is s5)  # May be False

# Basic operations
name = "World"
length = len(name)           # 5
first = name[0]              # 'W'
last = name[-1]              # 'd' (negative indexing!)
upper = name.upper()         # "WORLD"
lower = name.lower()         # "world"
contains = "or" in name      # True
index = name.index("o")      # 1 (raises ValueError if not found)
find = name.find("x")        # -1 (returns -1 if not found)
sub = name[1:4]              # "orl" (slicing)

# Multi-line strings
text = """This is
a multi-line
string"""

# Raw strings (no escape processing)
path = r"C:\Users\name\file"  # Backslashes are literal
regex = r"\d+\.\d+"           # Regex pattern without escaping

# Unicode
emoji = "Hello 🌍"
print(len(emoji))  # 8 (Python 3 counts code points)

# String repetition
dash_line = "-" * 50  # Creates string of 50 dashes

# ⚠️ Python strings are immutable
s = "hello"
# s[0] = "H"  # TypeError: 'str' object does not support item assignment
s = "H" + s[1:]  # Creates new string "Hello"
```

**TypeScript**
```typescript
// String creation
const s1: string = "Hello";
const s2: string = 'Hello';
const s3: string = `Hello`;  // Template literal

// Basic operations
const name: string = "World";
const length: number = name.length;      // 5
const first: string = name.charAt(0);    // 'W' or name[0]
const upper: string = name.toUpperCase(); // "WORLD"
const lower: string = name.toLowerCase(); // "world"
const contains: boolean = name.includes("or"); // true
const index: number = name.indexOf("o"); // 1
const sub: string = name.substring(1, 4); // "orl"
const sliced: string = name.slice(1, 4);  // "orl"

// Template literals - string interpolation
const greeting: string = `Hello, ${name}!`;
const multiLine: string = `
    Line 1
    Line 2
`;

// Tagged template literals (advanced)
function highlight(strings: TemplateStringsArray, ...values: any[]) {
    return strings.reduce((acc, str, i) =>
        acc + str + (values[i] ? `<mark>${values[i]}</mark>` : ''), '');
}
const highlighted = highlight`Name: ${name}, Length: ${length}`;
// "Name: <mark>World</mark>, Length: <mark>5</mark>"

// ⚠️ JavaScript/TypeScript string length counts UTF-16 code units
const emoji: string = "Hello 🌍";
console.log(emoji.length);  // 8 (🌍 = 2 UTF-16 code units!)

// Proper Unicode iteration
for (const char of emoji) {
    console.log(char);  // Properly handles surrogate pairs
}

// Get actual character count
const charCount = [...emoji].length;  // 7
```

**Go**
```go
// String creation
s1 := "Hello"
s2 := "Hello"
fmt.Println(s1 == s2)  // true (value comparison in Go)

// Go strings are immutable sequences of bytes
name := "World"
length := len(name)           // 5 (byte count!)
first := name[0]              // 87 (byte value of 'W')
firstChar := string(name[0])  // "W"
sub := name[1:4]              // "orl"

// String functions from "strings" package
import "strings"
upper := strings.ToUpper(name)         // "WORLD"
lower := strings.ToLower(name)         // "world"
contains := strings.Contains(name, "or") // true
index := strings.Index(name, "o")       // 1

// Raw strings (backticks)
path := `C:\Users\name\file`  // Backslashes are literal
multiLine := `Line 1
Line 2
Line 3`

// String formatting
greeting := fmt.Sprintf("Hello, %s!", name)

// ⚠️ CRITICAL: string vs []byte vs []rune
s := "Hello, 世界"
fmt.Println(len(s))           // 13 (bytes)
fmt.Println(len([]rune(s)))   // 9 (characters/runes)

// Byte iteration (wrong for Unicode!)
for i := 0; i < len(s); i++ {
    fmt.Printf("%c ", s[i])  // Garbled output for Chinese
}

// Correct: Rune iteration
for i, r := range s {
    fmt.Printf("%d: %c ", i, r)  // i is byte index, r is rune
}

// Or convert to []rune for indexing
runes := []rune(s)
fmt.Println(runes[7])  // '世' (correct!)
```

**SQL**
```sql
-- String literals
SELECT 'Hello';
SELECT "Hello";  -- Some DBs use double quotes

-- String functions (syntax varies by DB)
SELECT LENGTH('World');                    -- 5
SELECT UPPER('World');                     -- WORLD
SELECT LOWER('WORLD');                     -- world
SELECT SUBSTRING('World', 2, 3);          -- orl (position 2, length 3)
SELECT SUBSTR('World', 2, 3);             -- orl (Oracle/PostgreSQL)
SELECT LEFT('World', 2);                  -- Wo
SELECT RIGHT('World', 2);                 -- ld
SELECT TRIM('  hello  ');                 -- 'hello'
SELECT LTRIM('  hello');                  -- 'hello'
SELECT RTRIM('hello  ');                  -- 'hello'

-- String concatenation
SELECT 'Hello' || ' ' || 'World';         -- PostgreSQL/Oracle
SELECT CONCAT('Hello', ' ', 'World');     -- MySQL/SQL Server
SELECT 'Hello' + ' ' + 'World';           -- SQL Server

-- Pattern matching with LIKE
SELECT * FROM users WHERE name LIKE 'J%';   -- Starts with J
SELECT * FROM users WHERE name LIKE '%n';   -- Ends with n
SELECT * FROM users WHERE name LIKE '%oh%'; -- Contains 'oh'
SELECT * FROM users WHERE name LIKE 'J___'; -- J followed by 3 chars

-- Pattern matching with SIMILAR TO / REGEXP
SELECT * FROM users WHERE name ~ '^J.*n$';  -- PostgreSQL regex
SELECT * FROM users WHERE name REGEXP '^J.*n$'; -- MySQL

-- String position
SELECT POSITION('or' IN 'World');         -- 2 (1-indexed!)
SELECT INSTR('World', 'or');              -- 2 (Oracle/MySQL)
SELECT CHARINDEX('or', 'World');          -- 2 (SQL Server)

-- String replacement
SELECT REPLACE('Hello World', 'World', 'SQL');  -- 'Hello SQL'

-- COALESCE for null handling
SELECT COALESCE(name, 'Unknown') FROM users;

-- ⚠️ Collation affects comparison
SELECT 'A' = 'a';  -- Depends on collation!
-- Case-insensitive: Often TRUE
-- Binary collation: FALSE
```

**C++**
```cpp
#include <string>
#include <string_view>  // C++17
#include <format>       // C++20

// C-style strings (avoid in modern C++)
const char* cstr = "Hello";  // Null-terminated char array

// std::string (mutable!)
std::string s1 = "Hello";
std::string s2("Hello");
std::string s3 = s1;  // Copy

// Basic operations
std::string name = "World";
size_t length = name.length();     // or size()
char first = name[0];              // 'W' (no bounds check!)
char safe = name.at(0);            // 'W' (throws if out of bounds)
std::string upper = name;
std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);
std::string sub = name.substr(1, 3);  // "orl" (pos, length)

// ⚠️ C++ strings are MUTABLE
name[0] = 'w';  // Now "world"

// String search
size_t pos = name.find("or");      // 1
if (pos != std::string::npos) {
    // Found
}

// String modification (in-place)
name.append("!");               // "world!"
name.insert(0, "Hello ");       // "Hello world!"
name.replace(0, 5, "Hi");       // "Hi world!"
name.erase(2, 1);               // "Hiworld!" (remove space)

// Raw strings (C++11)
std::string path = R"(C:\Users\name\file)";  // Backslashes literal
std::string json = R"({
    "name": "John",
    "age": 30
})";

// std::string_view (C++17) - non-owning view
void process(std::string_view sv) {  // No copy!
    // Read-only operations only
}

// C++20 std::format
std::string greeting = std::format("Hello, {}!", name);

// Unicode handling (C++20 char8_t)
std::u8string utf8str = u8"Hello, 世界";

// ⚠️ CRITICAL: std::string length is in bytes for multi-byte chars
std::string emoji = "Hello 🌍";
std::cout << emoji.length();  // 10 (includes 4-byte emoji)
```

**Spark**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, concat, concat_ws, length, upper, lower,
    substring, trim, ltrim, rtrim, split, regexp_replace,
    regexp_extract, when, instr, locate
)

spark = SparkSession.builder.getOrCreate()

# Create DataFrame with string column
df = spark.createDataFrame([
    ("John Doe", "john@email.com"),
    ("Jane Smith", "jane@email.com"),
    ("Bob Wilson", None)
], ["name", "email"])

# Basic string operations
df.select(
    col("name"),
    length(col("name")).alias("name_length"),
    upper(col("name")).alias("upper_name"),
    lower(col("name")).alias("lower_name")
).show()

# String concatenation
df.select(
    concat(col("name"), lit(" - "), col("email")).alias("combined"),
    concat_ws(", ", col("name"), col("email")).alias("with_separator")
).show()

# Substring and splitting
df.select(
    substring(col("name"), 1, 4).alias("first_four"),  # 1-indexed!
    split(col("name"), " ")[0].alias("first_name"),
    split(col("name"), " ")[1].alias("last_name")
).show()

# Pattern matching with regexp
df.select(
    col("email"),
    regexp_extract(col("email"), r"([^@]+)@", 1).alias("username"),
    regexp_replace(col("email"), r"@.*", "@company.com").alias("new_email")
).show()

# Trimming
df.select(
    trim(col("name")),
    ltrim(col("name")),
    rtrim(col("name"))
).show()

# String contains and position
df.select(
    col("name"),
    col("name").contains("John").alias("has_john"),
    instr(col("name"), "o").alias("position_of_o"),  # 1-indexed, 0 if not found
    locate("o", col("name")).alias("also_position")  # Same as instr
).show()

# Conditional string operations
df.select(
    col("name"),
    when(col("name").startswith("J"), "J-name")
    .when(col("name").startswith("B"), "B-name")
    .otherwise("Other").alias("name_category")
).show()

# ⚠️ CRITICAL: Spark string operations are lazy transformations
# They execute only when an action is called (show, collect, write)
```

---

#### Pattern 2: String Immutability and StringBuilder Pattern

**Java**
```java
// ⚠️ String concatenation in loop - INEFFICIENT
String result = "";
for (int i = 0; i < 10000; i++) {
    result += i;  // Creates new String each iteration! O(n²)
}

// ✓ StringBuilder - EFFICIENT
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 10000; i++) {
    sb.append(i);  // Modifies internal buffer
}
String result = sb.toString();

// StringBuilder methods
StringBuilder builder = new StringBuilder("Hello");
builder.append(" World");        // "Hello World"
builder.insert(5, ",");          // "Hello, World"
builder.delete(5, 7);            // "HelloWorld"
builder.reverse();               // "dlroWolleH"
builder.setCharAt(0, 'D');       // "DlroWolleH"
String final = builder.toString();

// StringBuffer - thread-safe (slower)
StringBuffer threadSafe = new StringBuffer();
// Same methods as StringBuilder, but synchronized

// String.join (Java 8+) - preferred for simple cases
String csv = String.join(",", "a", "b", "c");  // "a,b,c"
List<String> items = Arrays.asList("x", "y", "z");
String joined = String.join("-", items);  // "x-y-z"

// Collectors.joining
List<String> words = Arrays.asList("Hello", "World");
String sentence = words.stream()
    .collect(Collectors.joining(" ", "[", "]"));  // "[Hello World]"
```

**Python**
```python
# ⚠️ String concatenation in loop - INEFFICIENT
result = ""
for i in range(10000):
    result += str(i)  # Creates new string each time! O(n²)

# ✓ List + join - EFFICIENT
parts = []
for i in range(10000):
    parts.append(str(i))
result = "".join(parts)

# ✓ Even better: List comprehension
result = "".join(str(i) for i in range(10000))

# io.StringIO for complex building
from io import StringIO
buffer = StringIO()
for i in range(10000):
    buffer.write(str(i))
result = buffer.getvalue()

# Practical joins
csv = ",".join(["a", "b", "c"])        # "a,b,c"
lines = "\n".join(["line1", "line2"])  # Multi-line string
path = "/".join(["home", "user", "file"])  # "home/user/file"

# ⚠️ Python CPython implementation detail:
# += may be optimized for single-reference strings
# But NEVER rely on this - always use join for loops
```

**TypeScript**
```typescript
// ⚠️ String concatenation in loop - INEFFICIENT
let result = "";
for (let i = 0; i < 10000; i++) {
    result += i;  // Creates new string each time
}

// ✓ Array + join - EFFICIENT
const parts: string[] = [];
for (let i = 0; i < 10000; i++) {
    parts.push(String(i));
}
result = parts.join("");

// Template literals for readability (small strings)
const name = "World";
const greeting = `Hello, ${name}!`;  // String interpolation

// Practical joins
const csv: string = ["a", "b", "c"].join(",");  // "a,b,c"
const path: string = ["home", "user", "file"].join("/");

// Array spread for combining
const combined = [...parts1, ...parts2].join("");
```

**Go**
```go
import (
    "strings"
    "bytes"
)

// ⚠️ String concatenation in loop - INEFFICIENT
result := ""
for i := 0; i < 10000; i++ {
    result += fmt.Sprintf("%d", i)  // Creates new string each time
}

// ✓ strings.Builder - EFFICIENT (Go 1.10+)
var builder strings.Builder
for i := 0; i < 10000; i++ {
    builder.WriteString(fmt.Sprintf("%d", i))
}
result := builder.String()

// With pre-allocation for better performance
var builder strings.Builder
builder.Grow(50000)  // Pre-allocate estimated capacity
for i := 0; i < 10000; i++ {
    builder.WriteString(fmt.Sprintf("%d", i))
}

// ✓ bytes.Buffer - also efficient
var buf bytes.Buffer
for i := 0; i < 10000; i++ {
    buf.WriteString(fmt.Sprintf("%d", i))
}
result := buf.String()

// strings.Join for slices
parts := []string{"a", "b", "c"}
csv := strings.Join(parts, ",")  // "a,b,c"

// ⚠️ + operator is fine for small, fixed concatenations
s := "Hello" + " " + "World"  // Compiler may optimize this
```

**C++**
```cpp
#include <string>
#include <sstream>
#include <numeric>  // For std::accumulate

// ⚠️ String concatenation in loop - MODERATELY EFFICIENT
// C++ strings are mutable, so += is reasonably efficient
std::string result;
for (int i = 0; i < 10000; i++) {
    result += std::to_string(i);  // May cause reallocations
}

// ✓ With reserve - MORE EFFICIENT
std::string result;
result.reserve(50000);  // Pre-allocate
for (int i = 0; i < 10000; i++) {
    result += std::to_string(i);
}

// std::ostringstream for complex building
std::ostringstream oss;
for (int i = 0; i < 10000; i++) {
    oss << i;
}
std::string result = oss.str();

// Joining with accumulate (C++17)
std::vector<std::string> parts = {"a", "b", "c"};
std::string csv = std::accumulate(
    std::next(parts.begin()), parts.end(),
    parts[0],
    [](const std::string& a, const std::string& b) {
        return a + "," + b;
    }
);  // "a,b,c"

// C++20 std::format
std::string greeting = std::format("Hello, {}!", name);
```

**Spark**
```python
from pyspark.sql.functions import concat, concat_ws, lit, collect_list, array_join

# Spark is immutable by design - transformations create new DataFrames

# Concatenating columns
df = df.withColumn(
    "full_info",
    concat(col("name"), lit(" <"), col("email"), lit(">"))
)

# Concatenating with separator
df = df.withColumn(
    "combined",
    concat_ws(" | ", col("name"), col("email"))
)

# Aggregating strings (group by and concatenate)
df.groupBy("department").agg(
    concat_ws(", ", collect_list("name")).alias("all_names")
).show()

# Array to string
df.withColumn(
    "name_parts",
    split(col("name"), " ")
).withColumn(
    "rejoined",
    array_join(col("name_parts"), "-")  # "John-Doe"
).show()
```

---

#### Pattern 3: String Formatting and Interpolation

**Java**
```java
// Java has NO native string interpolation (until Java 21 String Templates)

// Option 1: String.format (printf-style)
String name = "World";
int count = 42;
String s = String.format("Hello, %s! Count: %d", name, count);
// "Hello, World! Count: 42"

// Format specifiers
String.format("%s", "text");         // String
String.format("%d", 42);             // Integer
String.format("%f", 3.14159);        // Float: "3.141590"
String.format("%.2f", 3.14159);      // Float with precision: "3.14"
String.format("%10s", "hi");         // Right-padded: "        hi"
String.format("%-10s", "hi");        // Left-padded: "hi        "
String.format("%05d", 42);           // Zero-padded: "00042"
String.format("%x", 255);            // Hexadecimal: "ff"
String.format("%b", true);           // Boolean: "true"

// Option 2: MessageFormat (for i18n)
import java.text.MessageFormat;
String msg = MessageFormat.format(
    "Hello, {0}! You have {1} messages.",
    name, count
);

// Option 3: StringBuilder (manual)
StringBuilder sb = new StringBuilder();
sb.append("Hello, ").append(name).append("! Count: ").append(count);

// Java 21+ String Templates (Preview)
// String s = STR."Hello, \{name}! Count: \{count}";
```

**Python**
```python
name = "World"
count = 42
price = 19.99

# f-strings (Python 3.6+) - PREFERRED
s = f"Hello, {name}! Count: {count}"
# "Hello, World! Count: 42"

# f-string with expressions
s = f"Total: {count * price:.2f}"  # "Total: 839.58"

# f-string formatting
f"{name:>10}"      # Right-align:  "     World"
f"{name:<10}"      # Left-align:   "World     "
f"{name:^10}"      # Center:       "  World   "
f"{count:05d}"     # Zero-pad:     "00042"
f"{price:.2f}"     # 2 decimals:   "19.99"
f"{count:,}"       # Thousands:    "42"
f"{count:b}"       # Binary:       "101010"
f"{count:x}"       # Hex:          "2a"
f"{0.25:.0%}"      # Percent:      "25%"

# f-string with objects
class Person:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Person({self.name!r})"

p = Person("John")
f"{p}"     # "Person('John')"  - calls __str__ or __repr__
f"{p!r}"   # "Person('John')"  - forces __repr__
f"{p!s}"   # "Person('John')"  - forces __str__

# Debug format (Python 3.8+)
x = 10
f"{x=}"     # "x=10"
f"{x=:.2f}" # "x=10.00"

# format() method
"{}, {}!".format("Hello", "World")
"{0}, {1}!".format("Hello", "World")
"{greeting}, {name}!".format(greeting="Hello", name="World")

# % formatting (old style, avoid)
"Hello, %s! Count: %d" % (name, count)

# Performance: f-strings > format() > % formatting
```

**TypeScript**
```typescript
const name: string = "World";
const count: number = 42;
const price: number = 19.99;

// Template literals - Native interpolation
const s: string = `Hello, ${name}! Count: ${count}`;
// "Hello, World! Count: 42"

// Expressions in template literals
const total: string = `Total: ${(count * price).toFixed(2)}`;
// "Total: 839.58"

// Multi-line
const multiLine: string = `
  Name: ${name}
  Count: ${count}
  Price: $${price}
`;

// Tagged template literals for custom formatting
function currency(strings: TemplateStringsArray, ...values: number[]): string {
    return strings.reduce((result, str, i) => {
        const value = values[i];
        const formatted = value !== undefined
            ? `$${value.toFixed(2)}`
            : '';
        return result + str + formatted;
    }, '');
}

const amount = 42.5;
const formatted = currency`The total is ${amount}`;
// "The total is $42.50"

// For complex formatting, use Intl
const number = 1234567.89;
new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
    .format(number);  // "$1,234,567.89"

new Intl.NumberFormat('de-DE').format(number);  // "1.234.567,89"

// Padding
String(42).padStart(5, '0');  // "00042"
'hi'.padEnd(10);              // "hi        "
```

**Go**
```go
import "fmt"

name := "World"
count := 42
price := 19.99

// fmt.Sprintf - primary formatting function
s := fmt.Sprintf("Hello, %s! Count: %d", name, count)
// "Hello, World! Count: 42"

// Format verbs
fmt.Sprintf("%s", "text")      // String
fmt.Sprintf("%d", 42)          // Integer
fmt.Sprintf("%f", 3.14159)     // Float: "3.141590"
fmt.Sprintf("%.2f", 3.14159)   // Float with precision: "3.14"
fmt.Sprintf("%10s", "hi")      // Width 10, right-aligned: "        hi"
fmt.Sprintf("%-10s", "hi")     // Width 10, left-aligned: "hi        "
fmt.Sprintf("%05d", 42)        // Zero-padded: "00042"
fmt.Sprintf("%x", 255)         // Hex lowercase: "ff"
fmt.Sprintf("%X", 255)         // Hex uppercase: "FF"
fmt.Sprintf("%b", 42)          // Binary: "101010"
fmt.Sprintf("%t", true)        // Boolean: "true"
fmt.Sprintf("%v", anyValue)    // Default format
fmt.Sprintf("%+v", struct)     // With field names
fmt.Sprintf("%#v", value)      // Go syntax representation
fmt.Sprintf("%T", value)       // Type

// fmt.Printf - print directly
fmt.Printf("Hello, %s!\n", name)

// fmt.Fprintf - write to io.Writer
fmt.Fprintf(os.Stderr, "Error: %s\n", err)

// String concatenation with Sprintf
full := fmt.Sprintf("%s: %d items at $%.2f each", name, count, price)
```

**SQL**
```sql
-- String concatenation/formatting varies by database

-- PostgreSQL
SELECT format('Hello, %s! Count: %s', name, count) FROM table;
SELECT 'Hello, ' || name || '! Count: ' || count::text FROM table;

-- MySQL
SELECT CONCAT('Hello, ', name, '! Count: ', count) FROM table;
SELECT CONCAT_WS(' ', 'Hello,', name) FROM table;  -- With separator

-- SQL Server
SELECT CONCAT('Hello, ', name, '! Count: ', count) FROM table;
SELECT FORMAT(price, 'C')  -- Currency format: "$19.99"
SELECT FORMAT(date_col, 'yyyy-MM-dd') FROM table;

-- Oracle
SELECT 'Hello, ' || name || '! Count: ' || count FROM table;
SELECT TO_CHAR(price, '$999,999.99') FROM table;

-- Formatting numbers
SELECT FORMAT(1234.567, 2);           -- MySQL: "1234.57"
SELECT ROUND(1234.567, 2);            -- Most DBs: 1234.57
SELECT LPAD(CAST(42 AS CHAR), 5, '0'); -- "00042"
```

**C++**
```cpp
#include <string>
#include <sstream>
#include <iomanip>
#include <format>  // C++20

std::string name = "World";
int count = 42;
double price = 19.99;

// C++20 std::format - Modern approach
std::string s = std::format("Hello, {}! Count: {}", name, count);
// "Hello, World! Count: 42"

// Format specifiers (C++20)
std::format("{}", value);           // Default
std::format("{:10}", "hi");         // Width 10: "hi        "
std::format("{:>10}", "hi");        // Right-align: "        hi"
std::format("{:<10}", "hi");        // Left-align: "hi        "
std::format("{:^10}", "hi");        // Center: "    hi    "
std::format("{:05d}", 42);          // Zero-pad: "00042"
std::format("{:.2f}", 3.14159);     // Precision: "3.14"
std::format("{:x}", 255);           // Hex: "ff"
std::format("{:b}", 42);            // Binary: "101010"

// Pre-C++20: ostringstream
std::ostringstream oss;
oss << "Hello, " << name << "! Count: " << count;
std::string result = oss.str();

// With formatting manipulators
oss << std::fixed << std::setprecision(2) << price;  // "19.99"
oss << std::setw(10) << std::setfill('0') << count;  // "0000000042"
oss << std::hex << 255;                               // "ff"

// printf-style (C-style, works in C++)
char buffer[100];
snprintf(buffer, sizeof(buffer), "Hello, %s! Count: %d", name.c_str(), count);
std::string fromC = buffer;
```

---

#### Pattern 4: Go Strings vs []byte vs []rune (Unicode Handling)

**Go**
```go
// This is a CRITICAL distinction in Go!

s := "Hello, 世界!"  // String containing Chinese characters

// ============================================
// 1. string - Immutable byte sequence
// ============================================
fmt.Println(s)         // "Hello, 世界!"
fmt.Println(len(s))    // 14 (bytes, NOT characters!)

// String indexing returns bytes
fmt.Println(s[0])      // 72 (byte value of 'H')
fmt.Println(s[7])      // 228 (first byte of '世', NOT the character!)

// String slicing operates on bytes
fmt.Println(s[:5])     // "Hello"
fmt.Println(s[7:10])   // "世" (3 bytes for this Chinese char)
// ⚠️ s[7:8] would produce invalid UTF-8!

// ============================================
// 2. []byte - Mutable byte slice
// ============================================
// Use for: Binary data, file I/O, network protocols, performance

b := []byte(s)
fmt.Println(b)         // [72 101 108 108 111 44 32 228 184 150 231 149 140 33]
fmt.Println(len(b))    // 14

// Mutable!
b[0] = 'h'
fmt.Println(string(b)) // "hello, 世界!"

// Efficient for I/O
data, _ := os.ReadFile("file.txt")  // Returns []byte
os.WriteFile("file.txt", b, 0644)   // Takes []byte

// When to use []byte:
// - Reading/writing files
// - Network communication
// - Binary protocols
// - Performance-critical byte manipulation

// ============================================
// 3. []rune - Slice of Unicode code points
// ============================================
// Use for: Character-level string manipulation

r := []rune(s)
fmt.Println(r)         // [72 101 108 108 111 44 32 19990 30028 33]
fmt.Println(len(r))    // 10 (actual characters!)

// Safe character indexing
fmt.Println(string(r[7]))  // "世" (correct!)
fmt.Println(string(r[8]))  // "界" (correct!)

// Safe character manipulation
r[7] = '地'  // Replace character
fmt.Println(string(r))  // "Hello, 地界!"

// When to use []rune:
// - Character counting
// - Character-level indexing
// - Reversing strings (must use runes!)
// - Any operation on "characters"

// ============================================
// String Iteration
// ============================================

// WRONG: Byte iteration
for i := 0; i < len(s); i++ {
    fmt.Printf("%c", s[i])  // Garbled for non-ASCII
}

// CORRECT: Range iteration (yields runes)
for index, runeValue := range s {
    fmt.Printf("Index: %d, Rune: %c, Bytes: %d\n",
        index, runeValue, utf8.RuneLen(runeValue))
}
// Index: 0, Rune: H, Bytes: 1
// Index: 7, Rune: 世, Bytes: 3  // Note: index jumps from 6 to 7
// Index: 10, Rune: 界, Bytes: 3

// ============================================
// Practical Examples
// ============================================

// Reverse a string (MUST use runes!)
func reverseString(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}
fmt.Println(reverseString("Hello, 世界!"))  // "!界世 ,olleH"

// Count characters (not bytes)
func charCount(s string) int {
    return utf8.RuneCountInString(s)  // More efficient than len([]rune(s))
}
fmt.Println(charCount("Hello, 世界!"))  // 10

// Safe substring by character position
func substringByChar(s string, start, end int) string {
    runes := []rune(s)
    if start < 0 || end > len(runes) || start > end {
        return ""
    }
    return string(runes[start:end])
}
fmt.Println(substringByChar("Hello, 世界!", 7, 9))  // "世界"

// Check if string contains valid UTF-8
import "unicode/utf8"
if utf8.ValidString(s) {
    fmt.Println("Valid UTF-8")
}

// ============================================
// Performance Comparison
// ============================================
//
// string → []byte:  O(n) copy (but compiler may optimize)
// string → []rune:  O(n) copy + decode
// []byte → string:  O(n) copy
// []rune → string:  O(n) copy + encode
//
// For performance-critical code:
// - Work with []byte when possible
// - Convert to []rune only when character-level access needed
// - Avoid unnecessary conversions in loops
```

---

#### Pattern 5: Regular Expressions

**Java**
```java
import java.util.regex.Pattern;
import java.util.regex.Matcher;

String text = "Email: john@example.com, Phone: 123-456-7890";

// Compile pattern for reuse
Pattern emailPattern = Pattern.compile("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}");

// Check if matches
boolean matches = emailPattern.matcher("john@example.com").matches();  // true

// Find in string
Matcher matcher = emailPattern.matcher(text);
if (matcher.find()) {
    System.out.println(matcher.group());  // "john@example.com"
}

// Find all matches
Pattern phonePattern = Pattern.compile("\\d{3}-\\d{3}-\\d{4}");
Matcher phoneMatcher = phonePattern.matcher(text);
while (phoneMatcher.find()) {
    System.out.println(phoneMatcher.group());
}

// Capture groups
Pattern pattern = Pattern.compile("(\\w+)@(\\w+)\\.(\\w+)");
Matcher m = pattern.matcher("john@example.com");
if (m.find()) {
    System.out.println(m.group(0));  // "john@example.com" (full match)
    System.out.println(m.group(1));  // "john" (first group)
    System.out.println(m.group(2));  // "example" (second group)
    System.out.println(m.group(3));  // "com" (third group)
}

// Replace
String replaced = text.replaceAll("\\d", "*");  // Mask numbers
String replacedFirst = text.replaceFirst("\\d+", "XXX");

// Split
String[] parts = "a,b,,c".split(",");      // ["a", "b", "", "c"]
String[] parts2 = "a,b,,c".split(",", 2);  // ["a", "b,,c"] (limit splits)

// Flags
Pattern caseInsensitive = Pattern.compile("hello", Pattern.CASE_INSENSITIVE);
Pattern multiline = Pattern.compile("^line", Pattern.MULTILINE);
```

**Python**
```python
import re

text = "Email: john@example.com, Phone: 123-456-7890"

# Compile pattern for reuse
email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Check if matches (full string)
match = re.fullmatch(r'john@example\.com', 'john@example.com')  # Match object or None

# Search (find first match)
match = email_pattern.search(text)
if match:
    print(match.group())  # "john@example.com"

# Find all matches
emails = email_pattern.findall(text)  # List of strings

# Find all with match objects
for match in email_pattern.finditer(text):
    print(match.group(), match.start(), match.end())

# Capture groups
pattern = re.compile(r'(\w+)@(\w+)\.(\w+)')
match = pattern.search("john@example.com")
if match:
    print(match.group(0))   # "john@example.com"
    print(match.group(1))   # "john"
    print(match.groups())   # ('john', 'example', 'com')

# Named groups
pattern = re.compile(r'(?P<user>\w+)@(?P<domain>\w+)\.(?P<tld>\w+)')
match = pattern.search("john@example.com")
if match:
    print(match.group('user'))    # "john"
    print(match.groupdict())      # {'user': 'john', 'domain': 'example', 'tld': 'com'}

# Replace
replaced = re.sub(r'\d', '*', text)
replaced = re.sub(r'(\w+)@', r'\1-at-', text)  # Backreference
replaced = re.sub(r'\d+', lambda m: str(int(m.group()) * 2), text)  # Function

# Split
parts = re.split(r',\s*', "a, b,  c")  # ['a', 'b', 'c']

# Flags
re.search(r'hello', 'HELLO', re.IGNORECASE)
re.search(r'^line', text, re.MULTILINE)
re.search(r'hello\s+world', text, re.VERBOSE)  # Allow comments

# Raw strings are essential for regex!
# r'\d+' is '\d+', not '\\d+' (escaped backslash)
```

**TypeScript**
```typescript
const text = "Email: john@example.com, Phone: 123-456-7890";

// Regex literal
const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;

// RegExp constructor
const phoneRegex = new RegExp("\\d{3}-\\d{3}-\\d{4}");

// Test (returns boolean)
const isEmail = emailRegex.test("john@example.com");  // true

// Match (returns array or null)
const match = text.match(emailRegex);
if (match) {
    console.log(match[0]);  // "john@example.com"
}

// Global flag for all matches
const allEmails = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g);
// ["john@example.com"]

// Capture groups
const pattern = /(\w+)@(\w+)\.(\w+)/;
const groupMatch = "john@example.com".match(pattern);
if (groupMatch) {
    console.log(groupMatch[0]);  // "john@example.com"
    console.log(groupMatch[1]);  // "john"
    console.log(groupMatch[2]);  // "example"
}

// Named groups (ES2018)
const namedPattern = /(?<user>\w+)@(?<domain>\w+)\.(?<tld>\w+)/;
const namedMatch = "john@example.com".match(namedPattern);
if (namedMatch?.groups) {
    console.log(namedMatch.groups.user);  // "john"
}

// matchAll (returns iterator)
const regex = /\d+/g;
for (const match of text.matchAll(regex)) {
    console.log(match[0], match.index);
}

// Replace
const replaced = text.replace(/\d/g, '*');
const replaced2 = text.replace(/(\w+)@/, '$1-at-');
const replaced3 = text.replace(/\d+/g, (match) => String(Number(match) * 2));

// Split
const parts = "a, b,  c".split(/,\s*/);  // ["a", "b", "c"]

// Flags
const caseInsensitive = /hello/i;
const global = /hello/g;
const multiline = /^line/m;
const unicode = /\u{1F600}/u;  // Unicode flag for emoji
```

**Go**
```go
import "regexp"

text := "Email: john@example.com, Phone: 123-456-7890"

// Compile pattern (panics on invalid regex)
emailRegex := regexp.MustCompile(`[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`)

// Compile with error handling
emailRegex, err := regexp.Compile(`[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`)
if err != nil {
    // Handle error
}

// Match
matches := emailRegex.MatchString("john@example.com")  // true

// Find first match
match := emailRegex.FindString(text)  // "john@example.com"

// Find all matches
allMatches := emailRegex.FindAllString(text, -1)  // -1 for all matches

// Find with index
loc := emailRegex.FindStringIndex(text)  // [7 23] (start, end)

// Capture groups (submatch)
pattern := regexp.MustCompile(`(\w+)@(\w+)\.(\w+)`)
submatches := pattern.FindStringSubmatch("john@example.com")
// ["john@example.com", "john", "example", "com"]

// Named groups (Go uses (?P<name>...))
namedPattern := regexp.MustCompile(`(?P<user>\w+)@(?P<domain>\w+)\.(?P<tld>\w+)`)
match := namedPattern.FindStringSubmatch("john@example.com")
names := namedPattern.SubexpNames()
for i, name := range names {
    if i != 0 && name != "" {
        fmt.Printf("%s: %s\n", name, match[i])
    }
}

// Replace
replaced := emailRegex.ReplaceAllString(text, "[EMAIL]")
replaced2 := pattern.ReplaceAllString(text, "${1}-at-${2}.${3}")

// Replace with function
replaced3 := regexp.MustCompile(`\d+`).ReplaceAllStringFunc(text, func(s string) string {
    n, _ := strconv.Atoi(s)
    return strconv.Itoa(n * 2)
})

// Split
parts := regexp.MustCompile(`[,\s]+`).Split("a, b,  c", -1)

// ⚠️ Go regex doesn't support lookahead/lookbehind
// Use RE2 syntax, not PCRE
```

**SQL**
```sql
-- PostgreSQL (POSIX regex)
SELECT * FROM users WHERE email ~ '^[a-z]+@';           -- Match
SELECT * FROM users WHERE email ~* '^[A-Z]+@';          -- Case-insensitive
SELECT * FROM users WHERE email !~ '^admin';            -- Not match

SELECT REGEXP_REPLACE(email, '@.*', '@company.com') FROM users;
SELECT REGEXP_MATCHES(text, '\d+', 'g') FROM data;      -- All matches

-- MySQL
SELECT * FROM users WHERE email REGEXP '^[a-z]+@';
SELECT * FROM users WHERE email RLIKE '^[a-z]+@';       -- Synonym
SELECT REGEXP_REPLACE(email, '@.*', '@company.com') FROM users;  -- MySQL 8.0+
SELECT REGEXP_SUBSTR(text, '\\d+') FROM data;           -- MySQL 8.0+

-- SQL Server
-- No native regex! Use LIKE or CLR functions
SELECT * FROM users WHERE email LIKE '[a-z]%@%';        -- Limited patterns

-- Oracle
SELECT * FROM users WHERE REGEXP_LIKE(email, '^[a-z]+@');
SELECT REGEXP_REPLACE(email, '@.*', '@company.com') FROM users;
SELECT REGEXP_SUBSTR(text, '\d+') FROM data;
```

**Spark**
```python
from pyspark.sql.functions import regexp_extract, regexp_replace, rlike

# Match pattern
df.filter(col("email").rlike(r"^[a-z]+@")).show()

# Extract with regex
df.select(
    col("email"),
    regexp_extract(col("email"), r"([^@]+)@([^.]+)\.(.+)", 1).alias("user"),
    regexp_extract(col("email"), r"([^@]+)@([^.]+)\.(.+)", 2).alias("domain"),
    regexp_extract(col("email"), r"([^@]+)@([^.]+)\.(.+)", 3).alias("tld")
).show()

# Replace with regex
df.select(
    regexp_replace(col("email"), r"@.*", "@company.com").alias("new_email")
).show()

# Split with regex
from pyspark.sql.functions import split
df.select(
    split(col("text"), r"[,\s]+").alias("words")
).show()
```

---

## Section 3: Design Philosophy Links (설계 철학 링크)

### Official Documentation

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| **Java** | [java.lang.String](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html) | Immutability, String Pool |
| **Python** | [Text Sequence Type - str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str) | Unicode Strings, Methods |
| **TypeScript** | [Template Literals](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html) | String Types, Manipulation |
| **Go** | [Strings, bytes, runes](https://go.dev/blog/strings) | UTF-8 by Default |
| **SQL** | [PostgreSQL String Functions](https://www.postgresql.org/docs/current/functions-string.html) | Database-specific |
| **C++** | [std::string](https://en.cppreference.com/w/cpp/string/basic_string) | Mutable Strings |
| **Spark** | [String Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html) | Column Operations |

### Design Philosophy Quotes

> **Java**: "Strings are constant; their values cannot be changed after they are created."
> — Java Language Specification

String immutability enables the String Pool and thread safety without synchronization.

> **Go**: "A string holds arbitrary bytes. It is not required to hold Unicode text, UTF-8 text, or any other predefined format."
> — The Go Blog

Go treats strings as byte slices by default, requiring explicit rune handling for Unicode.

> **Python**: "Strings are immutable sequences of Unicode code points."
> — Python Documentation

Python 3 strings are always Unicode, eliminating the str/unicode confusion from Python 2.

---

## Section 4: Palantir Context Hint (팔란티어 맥락 힌트)

### 4.1 Foundry/OSDK String Patterns

**TypeScript OSDK String Manipulation:**
```typescript
import { Objects, Ontology } from "@foundry/ontology-api";

// Filtering with string patterns
const users = await Objects.search(User)
    .filter(user => user.email.contains("@company.com"))
    .all();

// String property access
const employee = await Objects.get(Employee, "EMP001");
const fullName = `${employee.firstName} ${employee.lastName}`;

// Ontology queries with string matching
const results = await Objects.search(Document)
    .filter(doc => doc.title.startsWith("Report"))
    .filter(doc => doc.status.equals("Published"))
    .orderBy(doc => doc.title.asc())
    .all();

// Aggregations with string grouping
const countByDepartment = await Objects.search(Employee)
    .groupBy(emp => emp.department)
    .count();
```

**Spark String Operations for Foundry Pipelines:**
```python
from transforms.api import transform, Input, Output
from pyspark.sql import functions as F

@transform(
    output=Output("/path/to/output"),
    source=Input("/path/to/source")
)
def compute(output, source):
    df = source.dataframe()

    # Common string operations in Foundry
    result = df.select(
        # Normalize text
        F.lower(F.trim(F.col("name"))).alias("normalized_name"),

        # Parse structured strings
        F.split(F.col("address"), ",")[0].alias("street"),

        # Extract patterns
        F.regexp_extract(F.col("phone"), r"(\d{3})-(\d{3})-(\d{4})", 0).alias("formatted_phone"),

        # Mask sensitive data
        F.regexp_replace(F.col("ssn"), r"\d{3}-\d{2}", "XXX-XX").alias("masked_ssn")
    )

    output.write_dataframe(result)
```

### 4.2 Interview Questions

1. **"Why is String immutable in Java?"**
   - Thread safety without synchronization
   - String pool/interning for memory optimization
   - Security (can't alter validated strings)
   - Hash code caching
   - Safe as HashMap keys

2. **"Go: string vs []byte vs []rune - when to use which?"**
   - `string`: General text, immutable, default choice
   - `[]byte`: Binary data, file I/O, network, performance-critical
   - `[]rune`: Character-level operations, Unicode handling
   - Key: `len(string)` returns bytes, not characters!

3. **"String concatenation performance - loop vs StringBuilder"**
   - Loop with `+=`: O(n^2) - creates new string each iteration
   - StringBuilder/join: O(n) - modifies buffer
   - Show knowledge of language-specific builders

4. **"Python: f-string vs format() - which is faster?"**
   - f-strings are faster (compile-time evaluation)
   - f-strings are more readable
   - format() useful for dynamic format strings
   - % formatting is legacy, avoid in new code

### 4.3 Common Interview Patterns

```python
# Pattern: Anagram Check
def are_anagrams(s1: str, s2: str) -> bool:
    from collections import Counter
    return Counter(s1.lower().replace(" ", "")) == Counter(s2.lower().replace(" ", ""))

# Pattern: Palindrome Check
def is_palindrome(s: str) -> bool:
    s = ''.join(c.lower() for c in s if c.isalnum())
    return s == s[::-1]

# Pattern: First Non-Repeating Character
def first_non_repeating(s: str) -> str:
    from collections import Counter
    counts = Counter(s)
    for c in s:
        if counts[c] == 1:
            return c
    return ""

# Pattern: Longest Common Prefix
def longest_common_prefix(strs: list[str]) -> str:
    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix

# Pattern: String Compression
def compress(s: str) -> str:
    result = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        result.append(s[i] + str(j - i))
        i = j
    compressed = ''.join(result)
    return compressed if len(compressed) < len(s) else s
```

---

## Section 5: Cross-References (상호 참조)

### Related Knowledge Bases

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F50** | Arrays & Lists | Strings as character arrays |
| **F02** | Mutability Patterns | String immutability concept |
| **F31** | Loops & Iteration | Iterating over string characters |
| **F22** | Type Coercion | String conversion rules |
| **F32** | Exception Handling | String parsing errors |
| **F60** | Streams & Functional | Functional string operations |

### Algorithm Patterns Using Strings

| Pattern | Description | Example |
|---------|-------------|---------|
| **Two Pointers** | Compare/manipulate from both ends | Palindrome check |
| **Sliding Window** | Fixed/variable size substring | Longest substring without repeats |
| **Hash Map** | Character frequency counting | Anagram check |
| **Trie** | Prefix-based operations | Autocomplete |
| **KMP/Rabin-Karp** | Pattern matching | Substring search |
| **Dynamic Programming** | Edit distance, LCS | Spell checker |

### String Time Complexity Cheatsheet

```
┌─────────────────────────────────────────────────────────────────┐
│                   STRING OPERATIONS COMPLEXITY                   │
├─────────────────────────────────────────────────────────────────┤
│ Operation              │ Immutable    │ Mutable (C++)           │
├─────────────────────────────────────────────────────────────────┤
│ Length                 │ O(1)         │ O(1)                    │
│ Access char at index   │ O(1)         │ O(1)                    │
│ Concatenation (+ once) │ O(n+m)       │ O(m) amortized          │
│ Concatenation (loop)   │ O(n²)        │ O(n) with reserve       │
│ Substring              │ O(k)         │ O(k)                    │
│ Search (indexOf)       │ O(n*m)       │ O(n*m)                  │
│ Replace all            │ O(n*m)       │ O(n)                    │
│ Compare (equals)       │ O(n)         │ O(n)                    │
│ Hash                   │ O(n)/O(1)*   │ O(n)                    │
├─────────────────────────────────────────────────────────────────┤
│ * Hash may be cached for immutable strings (Java)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary: String Cheatsheet

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STRING CHEATSHEET                            │
├─────────────────────────────────────────────────────────────────────┤
│ Immutable: Java, Python, TypeScript, Go, SQL, Spark                 │
│ Mutable:   C++ std::string                                          │
├─────────────────────────────────────────────────────────────────────┤
│ ENCODING:                                                           │
│ UTF-16: Java, JavaScript/TypeScript (internal)                      │
│ UTF-8:  Python 3, Go, Rust, most modern systems                     │
├─────────────────────────────────────────────────────────────────────┤
│ BUILDER PATTERN:                                                    │
│ Java:       StringBuilder.append()                                  │
│ Python:     [].append() + ''.join()                                 │
│ TypeScript: [].push() + join('')                                    │
│ Go:         strings.Builder.WriteString()                           │
│ C++:        ostringstream or string.reserve() + +=                  │
├─────────────────────────────────────────────────────────────────────┤
│ INTERPOLATION:                                                      │
│ Python:     f"Hello, {name}!"                                       │
│ TypeScript: `Hello, ${name}!`                                       │
│ Java:       String.format("Hello, %s!", name)                       │
│ Go:         fmt.Sprintf("Hello, %s!", name)                         │
│ C++20:      std::format("Hello, {}!", name)                         │
├─────────────────────────────────────────────────────────────────────┤
│ CRITICAL INTERVIEW TRAPS:                                           │
│ 1. Java: == compares references, equals() compares content          │
│ 2. Go: len(string) returns BYTES, not characters!                   │
│ 3. Python: += in loop is O(n²), use join()                          │
│ 4. JavaScript: length counts UTF-16 code units (emoji = 2)          │
│ 5. Go: Range over string yields (byte_index, rune)                  │
│ 6. SQL: Collation affects string comparison                         │
│ 7. C++: No bounds check with [], use at() for safety                │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
