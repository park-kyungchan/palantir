# F41: Parameters & Arguments (매개변수와 인자)

> **Concept ID**: `F41_parameters_arguments`
> **Universal Principle**: 함수에 데이터를 전달하는 메커니즘과 그 방식의 차이
> **Prerequisites**: F10_lexical_scope, F02_mutability_patterns

---

## 1. Universal Concept (언어 무관 개념 정의)

**Parameter(매개변수)**와 **Argument(인자)**는 함수에 데이터를 전달하는 핵심 메커니즘입니다.

**용어 구분 (중요!)**:
- **Parameter (Formal Parameter, 형식 매개변수)**: 함수 **정의**에 있는 변수 이름
- **Argument (Actual Argument, 실제 인자)**: 함수 **호출** 시 전달하는 실제 값

```
function greet(name) { ... }  // name = Parameter (형식 매개변수)
greet("Alice");               // "Alice" = Argument (실제 인자)
```

**전달 방식 (Passing Mechanisms)**:
1. **Pass by Value (값에 의한 전달)**: 값의 복사본 전달 - 원본 불변
2. **Pass by Reference (참조에 의한 전달)**: 원본 변수 자체 전달 - 원본 수정 가능
3. **Pass by Sharing (공유에 의한 전달)**: 객체 참조의 복사본 전달 - Java/Python 방식

**Mental Model**:
- **Parameters**: 함수라는 "기계"의 **입력 슬롯** (빈 소켓)
- **Arguments**: 슬롯에 실제로 **꽂는 플러그** (값)
- **Pass by Value**: 문서를 **복사해서** 전달 (원본 안전)
- **Pass by Reference**: 문서의 **원본** 자체를 전달 (수정 시 원본도 변경)
- **Pass by Sharing**: **명함**을 전달 (명함을 새로 쓸 순 있지만, 명함이 가리키는 사람은 수정 가능)

```
Pass by Value:     caller [42] ─복사→ function [42]  (두 개의 별개 값)
Pass by Reference: caller [x] ────→ function [x]    (같은 메모리)
Pass by Sharing:   caller [ref→Obj] ─복사→ function [ref→Obj] (ref는 별개, Obj는 공유)
```

**Why This Matters**:
- **버그 디버깅**: "왜 함수 호출 후 값이 바뀌었지?" 또는 "왜 안 바뀌었지?"
- **성능 최적화**: 큰 객체를 복사 vs 참조 전달의 성능 차이
- **API 설계**: 함수가 입력을 수정할 수 있는지 명확히 표현
- **면접 필수**: "Java는 Pass by Value인가 Reference인가?" (TRICK 질문!)

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Passing Mechanism** | Value (참조 복사) | Object Reference | Value (참조 복사) | Value Only | Value | Value/Ref/Ptr 선택 | Value (직렬화) |
| **Default Parameters** | No (오버로딩) | Yes | Yes | No (관용구 사용) | Yes | Yes (C++11+) | Yes |
| **Named Arguments** | No | Yes | No (객체로 대체) | No | Yes | No (C++20 designated) | Yes |
| **Variadic Params** | varargs `...` | `*args`, `**kwargs` | Rest `...` | `...` | N/A | Variadic templates | `*cols` |
| **Destructuring** | No (Record 패턴 Java 21+) | Yes | Yes | No | N/A | Yes (C++17 structured) | No |
| **Out Parameters** | 수동 (배열/래퍼) | 수동 (리스트/dict) | 수동 (객체) | Yes (multiple return) | OUT keyword | Yes (참조/포인터) | N/A |

### 2.2 Semantic Notes

---

#### **Passing Mechanism (전달 메커니즘)**

**Java - Pass by Value (Always!)**
```java
// Java는 항상 Pass by Value입니다. 참조 타입도 "참조의 복사본"을 전달합니다.

// 1. Primitive: 값 복사 (원본 불변)
void modifyPrimitive(int x) {
    x = 100;  // 로컬 복사본만 수정
}
int a = 10;
modifyPrimitive(a);
System.out.println(a);  // 10 (원본 불변)

// 2. Object: 참조 복사 (객체 내용은 수정 가능, 참조 자체는 교체 불가)
void modifyList(List<String> list) {
    list.add("added");     // 원본 객체 수정됨!
    list = new ArrayList<>();  // 로컬 참조만 변경, 원본 참조는 그대로
}
List<String> myList = new ArrayList<>();
myList.add("original");
modifyList(myList);
System.out.println(myList);  // [original, added] - 내용 수정됨

// 3. 불변 객체(String): "교체 불가"처럼 보이지만 원리는 같음
void modifyString(String s) {
    s = "changed";  // 새 String 객체에 로컬 참조 재할당
}
String str = "original";
modifyString(str);
System.out.println(str);  // "original" - String은 불변이라 새 객체 생성됨
```

**Python - Pass by Object Reference (Call by Sharing)**
```python
# Python은 "Pass by Object Reference" 또는 "Call by Sharing"입니다.
# 객체에 대한 참조가 복사되어 전달됩니다.

# 1. Immutable (int, str, tuple): 재할당 시 새 객체 생성
def modify_int(x):
    x = 100  # 새 int 객체에 바인딩, 원본 불변

a = 10
modify_int(a)
print(a)  # 10

# 2. Mutable (list, dict): 내부 수정 시 원본 변경됨
def modify_list(lst):
    lst.append("added")  # 원본 객체 수정!
    lst = ["new"]        # 로컬 바인딩만 변경

my_list = ["original"]
modify_list(my_list)
print(my_list)  # ["original", "added"]

# 3. 명시적 복사로 원본 보호
import copy
def safe_modify(lst):
    local_copy = copy.deepcopy(lst)
    local_copy.append("added")
    return local_copy
```

**TypeScript - Pass by Value (for primitives), Pass by Sharing (for objects)**
```typescript
// TypeScript/JavaScript: Java와 유사한 Pass by Sharing

// 1. Primitive: 값 복사
function modifyPrimitive(x: number): void {
    x = 100;  // 로컬 복사본만 수정
}
let a = 10;
modifyPrimitive(a);
console.log(a);  // 10

// 2. Object: 참조 공유 (내용 수정 가능)
function modifyObject(obj: { name: string }): void {
    obj.name = "changed";  // 원본 객체 수정됨!
    obj = { name: "new" }; // 로컬 참조만 변경
}
const myObj = { name: "original" };
modifyObject(myObj);
console.log(myObj.name);  // "changed"

// 3. Array spread로 얕은 복사
function safeModify(arr: number[]): number[] {
    const copy = [...arr];  // 얕은 복사
    copy.push(100);
    return copy;
}
```

**Go - Pass by Value (Always, Explicit)**
```go
// Go는 항상 Pass by Value입니다. 포인터도 "포인터 값"이 복사됩니다.

// 1. 기본 타입: 값 복사
func modifyInt(x int) {
    x = 100  // 로컬 복사본만 수정
}
a := 10
modifyInt(a)
fmt.Println(a)  // 10

// 2. 슬라이스: 헤더가 복사됨 (내부 배열은 공유!)
func modifySlice(s []int) {
    s[0] = 100  // 내부 배열 수정됨!
    s = append(s, 200)  // 로컬 슬라이스만 확장
}
slice := []int{1, 2, 3}
modifySlice(slice)
fmt.Println(slice)  // [100, 2, 3] - 첫 요소만 수정됨

// 3. 포인터로 명시적 참조 전달
func modifyWithPointer(x *int) {
    *x = 100  // 원본 수정
}
b := 10
modifyWithPointer(&b)
fmt.Println(b)  // 100

// 4. Struct는 완전 복사 (큰 struct는 포인터 권장)
type Person struct {
    Name string
    Age  int
}
func modifyPerson(p Person) {
    p.Name = "changed"  // 복사본만 수정
}
func modifyPersonPtr(p *Person) {
    p.Name = "changed"  // 원본 수정
}
```

**SQL - Pass by Value (Declarative)**
```sql
-- SQL은 선언적 언어로 "전달"보다는 "바인딩"에 가깝습니다

-- 1. 저장 프로시저 매개변수
CREATE PROCEDURE UpdateUser(
    IN user_id INT,              -- 입력 전용
    IN new_name VARCHAR(100),
    OUT result_count INT         -- 출력 전용
)
BEGIN
    UPDATE users SET name = new_name WHERE id = user_id;
    SELECT COUNT(*) INTO result_count FROM users WHERE name = new_name;
END;

-- 2. 함수 매개변수
CREATE FUNCTION GetUserName(user_id INT)
RETURNS VARCHAR(100)
BEGIN
    DECLARE result VARCHAR(100);
    SELECT name INTO result FROM users WHERE id = user_id;
    RETURN result;
END;

-- 3. 호출 시 바인딩
CALL UpdateUser(1, 'Alice', @count);
SELECT @count;
```

**C++ - Explicit Choice (Value/Reference/Pointer)**
```cpp
#include <iostream>
#include <vector>
using namespace std;

// 1. Pass by Value: 완전한 복사
void modifyByValue(int x) {
    x = 100;  // 복사본만 수정
}

// 2. Pass by Reference: 원본 직접 접근
void modifyByReference(int& x) {
    x = 100;  // 원본 수정!
}

// 3. Pass by Const Reference: 큰 객체의 효율적 읽기 전용 전달
void readOnly(const vector<int>& vec) {
    // vec.push_back(1);  // 컴파일 에러! const이므로 수정 불가
    cout << vec.size() << endl;
}

// 4. Pass by Pointer: 명시적 주소 전달
void modifyByPointer(int* x) {
    if (x != nullptr) {
        *x = 100;  // 원본 수정
    }
}

// 5. Smart Pointer 전달
void processShared(shared_ptr<int> ptr) {
    *ptr = 100;  // 공유 소유권, 원본 수정
}

int main() {
    int a = 10, b = 10, c = 10;

    modifyByValue(a);      // a = 10 (불변)
    modifyByReference(b);  // b = 100 (수정됨)
    modifyByPointer(&c);   // c = 100 (수정됨)

    return 0;
}
```

**Spark - Pass by Value (Serialization)**
```python
# Spark에서 클로저/UDF의 변수는 직렬화되어 executor로 전달됩니다

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType

spark = SparkSession.builder.getOrCreate()

# 1. 브로드캐스트 변수: 효율적인 읽기 전용 전달
lookup_dict = {"a": 1, "b": 2, "c": 3}
broadcast_lookup = spark.sparkContext.broadcast(lookup_dict)

@udf(IntegerType())
def lookup_value(key):
    return broadcast_lookup.value.get(key, 0)

# 2. UDF 파라미터: 직렬화되어 전달
multiplier = 10  # driver 변수

@udf(IntegerType())
def multiply(x):
    return x * multiplier  # multiplier가 직렬화됨

# 3. 주의: driver 변수 수정은 executor에 반영 안 됨!
counter = 0
def bad_counter(x):
    global counter
    counter += 1  # driver의 counter는 변경 안 됨!
    return x

# 4. Accumulator 사용 (올바른 방법)
counter_acc = spark.sparkContext.accumulator(0)
def good_counter(x):
    counter_acc.add(1)
    return x
```

---

#### **Default Parameters (기본 매개변수)**

**Java - No Default Parameters (Use Overloading)**
```java
// Java는 기본 매개변수를 지원하지 않습니다. 메서드 오버로딩으로 대체합니다.

public class Greeter {
    // 오버로딩으로 기본값 흉내내기
    public void greet() {
        greet("World");
    }

    public void greet(String name) {
        greet(name, "Hello");
    }

    public void greet(String name, String greeting) {
        System.out.println(greeting + ", " + name + "!");
    }
}

// Builder 패턴으로 선택적 매개변수 처리
public class Request {
    private final String url;
    private final int timeout;
    private final boolean retry;

    private Request(Builder builder) {
        this.url = builder.url;
        this.timeout = builder.timeout;
        this.retry = builder.retry;
    }

    public static class Builder {
        private final String url;      // 필수
        private int timeout = 30000;   // 기본값
        private boolean retry = true;  // 기본값

        public Builder(String url) {
            this.url = url;
        }

        public Builder timeout(int val) { timeout = val; return this; }
        public Builder retry(boolean val) { retry = val; return this; }
        public Request build() { return new Request(this); }
    }
}

// 사용
Request req = new Request.Builder("https://api.example.com")
    .timeout(5000)
    .build();
```

**Python - Full Default Parameter Support**
```python
# Python은 완전한 기본 매개변수를 지원합니다

def greet(name="World", greeting="Hello"):
    print(f"{greeting}, {name}!")

greet()                    # Hello, World!
greet("Alice")            # Hello, Alice!
greet("Bob", "Hi")        # Hi, Bob!
greet(greeting="Hey")     # Hey, World! (키워드 인자)

# ⚠️ CRITICAL: Mutable Default Argument Trap (면접 필수!)
def bad_append(item, lst=[]):  # 리스트가 함수 정의 시 한 번만 생성됨!
    lst.append(item)
    return lst

print(bad_append(1))  # [1]
print(bad_append(2))  # [1, 2] - 예상: [2]인데 [1, 2]!
print(bad_append(3))  # [1, 2, 3] - 계속 누적됨!

# 올바른 패턴: None을 사용
def good_append(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst

print(good_append(1))  # [1]
print(good_append(2))  # [2] - 올바르게 새 리스트 생성
```

**TypeScript - Default and Optional Parameters**
```typescript
// TypeScript: 기본값과 선택적 매개변수 모두 지원

// 1. 기본값
function greet(name: string = "World", greeting: string = "Hello"): string {
    return `${greeting}, ${name}!`;
}

greet();                 // "Hello, World!"
greet("Alice");          // "Hello, Alice!"
greet("Bob", "Hi");      // "Hi, Bob!"

// 2. 선택적 매개변수 (Optional)
function greetOptional(name?: string): string {
    return `Hello, ${name ?? "World"}!`;
}

greetOptional();         // "Hello, World!"
greetOptional(undefined); // "Hello, World!"
greetOptional("Alice");  // "Hello, Alice!"

// 3. undefined vs 기본값 차이
function demo(x: string = "default"): void {
    console.log(x);
}
demo();           // "default"
demo(undefined);  // "default" (기본값 적용됨!)

// 4. 객체 구조분해로 "Named Parameters" 흉내
interface GreetOptions {
    name?: string;
    greeting?: string;
    excited?: boolean;
}

function greetWithOptions({
    name = "World",
    greeting = "Hello",
    excited = false
}: GreetOptions = {}): string {
    const punct = excited ? "!" : ".";
    return `${greeting}, ${name}${punct}`;
}

greetWithOptions();                          // "Hello, World."
greetWithOptions({ name: "Alice" });         // "Hello, Alice."
greetWithOptions({ excited: true });         // "Hello, World!"
greetWithOptions({ name: "Bob", excited: true }); // "Hello, Bob!"
```

**Go - No Default Parameters (Use Idioms)**
```go
// Go는 기본 매개변수를 지원하지 않습니다. 관용구로 대체합니다.

// 1. 함수 옵션 패턴 (Functional Options)
type Server struct {
    host    string
    port    int
    timeout time.Duration
}

type ServerOption func(*Server)

func WithPort(port int) ServerOption {
    return func(s *Server) {
        s.port = port
    }
}

func WithTimeout(d time.Duration) ServerOption {
    return func(s *Server) {
        s.timeout = d
    }
}

func NewServer(host string, opts ...ServerOption) *Server {
    s := &Server{
        host:    host,
        port:    8080,           // 기본값
        timeout: 30 * time.Second, // 기본값
    }
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// 사용
s1 := NewServer("localhost")                           // 기본값 사용
s2 := NewServer("localhost", WithPort(9090))           // port만 변경
s3 := NewServer("localhost", WithPort(9090), WithTimeout(60*time.Second))

// 2. 설정 구조체 패턴
type Config struct {
    Host    string
    Port    int
    Timeout time.Duration
}

func DefaultConfig() Config {
    return Config{
        Host:    "localhost",
        Port:    8080,
        Timeout: 30 * time.Second,
    }
}

func NewServerWithConfig(cfg Config) *Server {
    return &Server{host: cfg.Host, port: cfg.Port, timeout: cfg.Timeout}
}

// 사용
cfg := DefaultConfig()
cfg.Port = 9090
s := NewServerWithConfig(cfg)
```

**SQL - Default Parameter Values**
```sql
-- SQL 저장 프로시저/함수에서 기본값 지원

-- MySQL
CREATE PROCEDURE GetUsers(
    IN status VARCHAR(20) DEFAULT 'active',
    IN limit_count INT DEFAULT 10
)
BEGIN
    SELECT * FROM users
    WHERE status = status
    LIMIT limit_count;
END;

CALL GetUsers();              -- 기본값 사용
CALL GetUsers('inactive');    -- status만 지정
CALL GetUsers('all', 50);     -- 둘 다 지정

-- PostgreSQL
CREATE FUNCTION get_users(
    status TEXT DEFAULT 'active',
    limit_count INT DEFAULT 10
)
RETURNS TABLE(id INT, name TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.name FROM users u
    WHERE u.status = get_users.status
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

SELECT * FROM get_users();                -- 기본값 사용
SELECT * FROM get_users('inactive');      -- status만 지정
SELECT * FROM get_users(limit_count := 5); -- Named parameter (PostgreSQL)
```

**C++ - Default Arguments (C++11+)**
```cpp
#include <string>
using namespace std;

// 1. 함수 기본 인자 (오른쪽부터 연속으로)
void greet(string name = "World", string greeting = "Hello") {
    cout << greeting << ", " << name << "!" << endl;
}

greet();                  // Hello, World!
greet("Alice");           // Hello, Alice!
greet("Bob", "Hi");       // Hi, Bob!

// 2. 주의: 왼쪽에 기본값 있으면 오른쪽도 필수
// void bad(int a = 1, int b);  // 컴파일 에러!
void good(int a, int b = 2);    // OK

// 3. 선언과 정의 분리 시 선언에만 기본값
// header.h
void process(int x, int y = 10);

// source.cpp
void process(int x, int y) {  // 정의에는 기본값 없음
    // ...
}

// 4. nullptr로 선택적 포인터 매개변수
void log(const string& msg, ostream* out = nullptr) {
    if (out) {
        *out << msg << endl;
    } else {
        cout << msg << endl;
    }
}
```

**Spark - Default Parameters in UDFs**
```python
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

# Python UDF에서 기본 매개변수 사용
def greet_with_default(name, greeting="Hello"):
    return f"{greeting}, {name}!"

greet_udf = udf(greet_with_default, StringType())

# DataFrame 컬럼에 적용
df.withColumn("greeting", greet_udf(df["name"]))

# 기본값 오버라이드
from pyspark.sql.functions import lit
df.withColumn("greeting", greet_udf(df["name"], lit("Hi")))
```

---

#### **Named Arguments (명명된 인자)**

**Python - Full Named Argument Support**
```python
def create_user(name, age, email, active=True):
    return {
        "name": name,
        "age": age,
        "email": email,
        "active": active
    }

# 위치 인자
create_user("Alice", 30, "alice@example.com")

# 키워드 인자 (순서 무관)
create_user(email="bob@example.com", name="Bob", age=25)

# 혼합 (위치 인자가 먼저)
create_user("Charlie", age=35, email="charlie@example.com")

# Keyword-only 매개변수 (* 뒤)
def configure(*, host, port, ssl=False):  # *를 사용해서 keyword-only 강제
    pass

# configure("localhost", 8080)  # TypeError!
configure(host="localhost", port=8080)  # OK

# Positional-only 매개변수 (Python 3.8+, / 앞)
def greet(name, /, greeting="Hello"):  # name은 위치로만 전달 가능
    print(f"{greeting}, {name}!")

greet("Alice")              # OK
# greet(name="Alice")       # TypeError!
greet("Alice", greeting="Hi")  # OK
```

**SQL - Named Parameters**
```sql
-- PostgreSQL: Named notation
SELECT * FROM get_users(status := 'active', limit_count := 5);

-- SQL Server: Named parameters
EXEC GetUsers @status = 'active', @limit = 5;

-- Oracle: Named notation
CALL get_users(p_status => 'active', p_limit => 5);

-- MySQL: 이름 지정 미지원, 순서로만 전달
CALL GetUsers('active', 5);
```

**TypeScript/Java/Go/C++ - Object Pattern for Named Arguments**
```typescript
// TypeScript: 객체 구조분해로 명명된 인자 흉내
interface UserOptions {
    name: string;
    age: number;
    email: string;
    active?: boolean;
}

function createUser({ name, age, email, active = true }: UserOptions) {
    return { name, age, email, active };
}

// 호출 시 프로퍼티 이름으로 명확하게 전달
createUser({ name: "Alice", age: 30, email: "alice@example.com" });
createUser({ email: "bob@example.com", name: "Bob", age: 25 }); // 순서 무관
```

```java
// Java: Builder 패턴으로 명명된 인자 흉내
User user = User.builder()
    .name("Alice")
    .age(30)
    .email("alice@example.com")
    .build();

// Java 14+ Record로 간단한 케이스
record UserParams(String name, int age, String email) {}
User.create(new UserParams("Alice", 30, "alice@example.com"));
```

---

#### **Variadic Parameters (가변 인자)**

**Java - Varargs**
```java
// varargs: 타입... 문법
public static int sum(int... numbers) {
    int total = 0;
    for (int n : numbers) {
        total += n;
    }
    return total;
}

sum();           // 0
sum(1);          // 1
sum(1, 2, 3);    // 6
sum(new int[]{1, 2, 3, 4}); // 배열도 가능

// varargs는 마지막 매개변수여야 함
public static void log(String level, String... messages) {
    for (String msg : messages) {
        System.out.println("[" + level + "] " + msg);
    }
}

// 주의: varargs vs 배열
public void withVarargs(String... args) { }  // 호출: f("a", "b")
public void withArray(String[] args) { }     // 호출: f(new String[]{"a", "b"})
```

**Python - *args and **kwargs**
```python
# *args: 위치 가변 인자 (튜플로 수집)
def sum_all(*numbers):
    return sum(numbers)

sum_all(1, 2, 3)    # 6
sum_all()           # 0

# **kwargs: 키워드 가변 인자 (딕셔너리로 수집)
def create_user(**kwargs):
    return kwargs

create_user(name="Alice", age=30)  # {'name': 'Alice', 'age': 30}

# 혼합: 순서 규칙 (위치 -> *args -> 키워드 -> **kwargs)
def complex_func(required, *args, option=None, **kwargs):
    print(f"required: {required}")
    print(f"args: {args}")
    print(f"option: {option}")
    print(f"kwargs: {kwargs}")

complex_func("must", 1, 2, 3, option="opt", extra="value")
# required: must
# args: (1, 2, 3)
# option: opt
# kwargs: {'extra': 'value'}

# Unpacking: *와 **로 시퀀스/딕셔너리 풀기
numbers = [1, 2, 3]
sum_all(*numbers)  # sum_all(1, 2, 3)과 동일

config = {"name": "Alice", "age": 30}
create_user(**config)  # create_user(name="Alice", age=30)과 동일
```

**TypeScript - Rest Parameters**
```typescript
// Rest parameter: ...name: Type[]
function sum(...numbers: number[]): number {
    return numbers.reduce((a, b) => a + b, 0);
}

sum(1, 2, 3);    // 6
sum();           // 0

// Rest는 마지막 매개변수여야 함
function log(level: string, ...messages: string[]): void {
    messages.forEach(msg => console.log(`[${level}] ${msg}`));
}

// Spread operator: 배열 풀기
const nums = [1, 2, 3];
sum(...nums);  // sum(1, 2, 3)과 동일

// Rest vs Spread 구분
// Rest: 함수 정의에서 여러 인자를 배열로 수집
// Spread: 함수 호출에서 배열을 여러 인자로 풀기
```

**Go - Variadic Functions**
```go
// 가변 인자: ...Type
func sum(numbers ...int) int {
    total := 0
    for _, n := range numbers {
        total += n
    }
    return total
}

sum(1, 2, 3)    // 6
sum()           // 0

// 슬라이스 전달: ...으로 풀기
nums := []int{1, 2, 3}
sum(nums...)    // sum(1, 2, 3)과 동일

// interface{}로 모든 타입 가변 인자
func printAll(args ...interface{}) {
    for _, arg := range args {
        fmt.Printf("%v ", arg)
    }
}

printAll(1, "hello", true, 3.14)  // 1 hello true 3.14
```

**C++ - Variadic Templates (C++11+)**
```cpp
#include <iostream>
using namespace std;

// 1. 재귀 템플릿으로 가변 인자
// Base case
void print() {
    cout << endl;
}

// Recursive case
template<typename T, typename... Args>
void print(T first, Args... rest) {
    cout << first << " ";
    print(rest...);
}

print(1, "hello", 3.14);  // 1 hello 3.14

// 2. Fold expressions (C++17)
template<typename... Args>
auto sum(Args... args) {
    return (args + ...);  // 우측 fold
}

sum(1, 2, 3);  // 6

// 3. C-style variadic (권장하지 않음)
#include <cstdarg>
int oldSum(int count, ...) {
    va_list args;
    va_start(args, count);
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += va_arg(args, int);
    }
    va_end(args);
    return total;
}
```

**Spark - Variadic Column Arguments**
```python
from pyspark.sql.functions import col, concat, coalesce

# *cols 패턴: 여러 컬럼 인자
df.select("name", "age", "email")          # 문자열로 여러 컬럼
df.select(col("name"), col("age"))         # Column 객체로

# concat은 가변 인자 함수
df.select(concat(col("first"), col("last")))

# coalesce: 첫 번째 non-null 값
df.select(coalesce(col("primary"), col("secondary"), col("default")))

# 동적으로 컬럼 리스트 전달
columns = ["name", "age", "email"]
df.select(*columns)  # Python unpacking
df.select([col(c) for c in columns])  # Column 객체 리스트
```

---

#### **Destructuring Parameters (구조분해 매개변수)**

**Python - Tuple/Dict Unpacking**
```python
# 튜플 구조분해
def process_point(point):
    x, y = point  # 함수 내부에서 언패킹
    return x + y

# 또는 직접 매개변수에서
def process_point_direct((x, y)):  # Python 2 문법 (3에서 제거됨)
    return x + y

# Python 3 방식: * 연산자로 확장 언패킹
def head_and_tail(first, *rest):
    return first, rest

head_and_tail(1, 2, 3, 4)  # (1, (2, 3, 4))

# 딕셔너리 구조분해 (함수 시그니처에서는 불가, 내부에서)
def process_user(user):
    name, age = user['name'], user['age']
    # 또는
    name = user.get('name', 'Unknown')
```

**TypeScript - Full Destructuring Support**
```typescript
// 배열 구조분해
function processPoint([x, y]: [number, number]): number {
    return x + y;
}

processPoint([10, 20]);  // 30

// 객체 구조분해
function greetUser({ name, age }: { name: string; age: number }): string {
    return `Hello, ${name}! You are ${age}.`;
}

greetUser({ name: "Alice", age: 30 });

// 기본값과 함께
function createUser({
    name = "Anonymous",
    age = 0,
    active = true
}: Partial<{ name: string; age: number; active: boolean }> = {}): void {
    console.log({ name, age, active });
}

createUser();                    // { name: "Anonymous", age: 0, active: true }
createUser({ name: "Alice" });   // { name: "Alice", age: 0, active: true }

// 중첩 구조분해
function processNested({
    user: { name, address: { city } }
}: {
    user: { name: string; address: { city: string } }
}): string {
    return `${name} from ${city}`;
}

processNested({ user: { name: "Alice", address: { city: "Seoul" } } });
```

**C++ - Structured Bindings (C++17)**
```cpp
#include <tuple>
#include <map>
using namespace std;

// 튜플 구조분해
tuple<int, string, double> getData() {
    return {1, "hello", 3.14};
}

void process() {
    auto [id, name, value] = getData();
    // id = 1, name = "hello", value = 3.14
}

// pair 구조분해
void processMap() {
    map<string, int> ages = {{"Alice", 30}, {"Bob", 25}};

    for (auto& [name, age] : ages) {
        cout << name << ": " << age << endl;
    }
}

// struct 구조분해
struct Point { int x; int y; };

void processPoint(Point p) {
    auto [x, y] = p;
    cout << x << ", " << y << endl;
}
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS 8.4.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.4.1) | Formal Parameters |
| Python | [Function Definitions](https://docs.python.org/3/reference/compound_stmts.html#function-definitions) | Default arguments, *args, **kwargs |
| TypeScript | [Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html) | Optional/Default/Rest Parameters |
| Go | [Function Types](https://go.dev/ref/spec#Function_types) | Variadic parameters |
| SQL | [CREATE PROCEDURE](https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html) | IN, OUT, INOUT parameters |
| C++ | [Function Parameters](https://en.cppreference.com/w/cpp/language/function) | Default arguments, parameter packs |
| Spark | [UDF Guide](https://spark.apache.org/docs/latest/sql-ref-functions-udf-scalar.html) | User-defined function parameters |

---

## 4. Palantir Context Hint

**Foundry/OSDK Relevance**:
- **TypeScript OSDK**: 선택적 매개변수 vs `undefined` 처리 주의
  ```typescript
  // OSDK 함수 호출 시 undefined와 미전달의 차이
  osdk.myAction({ param: undefined });  // param 명시적 undefined
  osdk.myAction({ });                   // param 미전달 (기본값 적용)
  ```
- **Spark UDF**: 매개변수 직렬화 주의 - 큰 객체는 브로드캐스트 사용
- **Python Transforms**: 가변 인자 함수의 타입 힌트 필수

**Interview Relevance (면접 필수!)**:

1. **"Java는 Pass by Value인가 Pass by Reference인가?"**
   - **정답**: 항상 Pass by Value
   - **함정**: 객체를 전달하면 수정되니까 Reference 아닌가요?
   - **설명**: 객체의 "참조(주소)"가 값으로 복사됨. 참조가 가리키는 객체는 수정 가능하지만, 참조 자체를 다른 객체로 바꿀 수는 없음

2. **"Python의 Mutable Default Argument 버그를 설명하세요"**
   ```python
   # 버그 코드
   def append_to(element, lst=[]):
       lst.append(element)
       return lst

   append_to(1)  # [1]
   append_to(2)  # [1, 2] - 버그!

   # 이유: 기본값 []는 함수 정의 시 한 번만 생성됨
   # 해결: None 패턴
   def append_to(element, lst=None):
       if lst is None:
           lst = []
       lst.append(element)
       return lst
   ```

3. **"Go에서 Optional Parameter를 어떻게 구현하나요?"**
   - **정답**: Functional Options 패턴 또는 Config 구조체
   - Go는 의도적으로 기본 매개변수를 지원하지 않음 (명시성 강조)

4. **"Rest Parameter와 Spread Operator의 차이는?"**
   - **Rest**: 함수 **정의**에서 여러 인자를 배열로 **수집** `function f(...args)`
   - **Spread**: 함수 **호출**에서 배열을 여러 인자로 **전개** `f(...array)`

5. **"C++에서 const 참조 매개변수는 언제 사용하나요?"**
   - 큰 객체를 복사 없이 읽기 전용으로 전달할 때
   - `void process(const std::vector<int>& data)` - 복사 비용 없이 안전하게 전달

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F40_function_declarations (함수 정의와 선언)
- → F02_mutability_patterns (가변성과 매개변수 전달의 관계)
- → F42_return_values (반환값과 출력 매개변수)
- → F44_closures (클로저와 캡처된 변수)
- → F11_closure_capture (클로저 캡처 메커니즘)
- → F24_generics_polymorphism (제네릭 매개변수)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00b_functions_and_scope (함수와 스코프 기초)
- → 21_python_backend_async (Python 비동기 함수 매개변수)
- → 20_go_services_and_concurrency (Go 함수 패턴)
- → 22_java_kotlin_backend_foundations (Java 메서드 매개변수)

---

## 6. Quick Cheat Sheet (빠른 참조)

### 언어별 전달 메커니즘 요약

| 언어 | Primitive | Object | 수정 영향 | 교체 영향 |
|------|-----------|--------|-----------|-----------|
| **Java** | 값 복사 | 참조 복사 | 원본 수정됨 | 원본 불변 |
| **Python** | 바인딩 복사 | 참조 공유 | 원본 수정됨 | 원본 불변 |
| **TypeScript** | 값 복사 | 참조 복사 | 원본 수정됨 | 원본 불변 |
| **Go** | 값 복사 | 값 복사 | 포인터 필요 | 포인터 필요 |
| **C++** | 명시적 선택 | 명시적 선택 | 참조/포인터 시 | 참조/포인터 시 |

### 기본 매개변수 패턴

```
Java:       오버로딩 또는 Builder 패턴
Python:     def f(x, y=10):
TypeScript: function f(x: number, y: number = 10):
Go:         Functional Options 또는 Config 구조체
C++:        void f(int x, int y = 10);
SQL:        IN param INT DEFAULT 10
```

### 가변 인자 문법

```
Java:       void f(String... args)
Python:     def f(*args, **kwargs):
TypeScript: function f(...args: string[]):
Go:         func f(args ...int)
C++:        template<typename... Args> void f(Args... args)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
