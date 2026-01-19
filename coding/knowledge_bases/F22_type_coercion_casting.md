# F22: Type Coercion & Casting (타입 강제 변환과 캐스팅)

> **Concept ID**: `F22_type_coercion_casting`
> **Universal Principle**: 한 타입에서 다른 타입으로 변환하는 암시적/명시적 메커니즘
> **Prerequisites**: F20_static_vs_dynamic_typing

---

## 1. Universal Concept (언어 무관 개념 정의)

**타입 변환**은 데이터를 한 타입에서 다른 타입으로 바꾸는 과정입니다. 이 과정은 두 가지 방식으로 일어납니다:

### Coercion (암시적 변환) vs Casting (명시적 변환)

| 종류 | 정의 | 예시 |
|------|------|------|
| **Coercion** | 컴파일러/인터프리터가 자동으로 수행 | `"5" + 3` → `"53"` (JS) |
| **Casting** | 개발자가 명시적으로 요청 | `(int) 3.14` → `3` (Java) |

### Widening vs Narrowing 변환

```
Widening (확장 변환) - 안전함
   int → long → float → double
   byte → short → int
   정보 손실 없음 (보통)

Narrowing (축소 변환) - 위험함
   double → float → long → int
   long → short → byte
   정보 손실 가능!
```

**Mental Model**:
```
데이터 크기와 변환 방향:

작은 타입 ────── Widening (자동) ─────→ 큰 타입
  int 32bit                              long 64bit
     ✓ 안전: int → long (암시적 OK)

큰 타입 ────── Narrowing (명시적) ─────→ 작은 타입
  long 64bit                              int 32bit
     ⚠ 위험: long → int (명시적 필요, 데이터 손실)
```

### Type Safety Implications

1. **정밀도 손실**: `double → float` 시 소수점 자릿수 손실
2. **오버플로우**: `long → int` 시 범위 초과 값이 잘림
3. **의미론적 오류**: `"123abc" → int` 파싱 실패
4. **NULL/undefined 처리**: 강제 변환 중 예외 발생

**Why This Matters**:
- JavaScript `==`의 암시적 변환으로 인한 예측 불가능한 동작
- 금융 계산에서 부동소수점 변환으로 인한 정밀도 손실
- 데이터 파이프라인에서 타입 불일치로 인한 런타임 오류
- 보안 취약점: 정수 오버플로우 공격

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Implicit Coercion** | 제한적 (widening만) | 문자열 concat, bool | truthy/falsy, ==, + | 없음 (strict) | 많음 (비교, 연산) | 많음 (산술, 포인터) | 많음 (스키마 추론) |
| **Explicit Cast Syntax** | `(Type)value` | `int()`, `str()`, `float()` | `as Type`, `<Type>` | `Type(value)` | `CAST(x AS Type)` | `static_cast<T>()` 등 | `.cast(Type)` |
| **Safe Cast Option** | `instanceof` 체크 | `isinstance()` | Type guards | Type assertions | `TRY_CAST()` (일부 DB) | `dynamic_cast` | `.try_cast()` 없음 |
| **Null/None Handling** | NPE 위험 | None → "None" 문자열 | `as` nullish 통과 | 제로값으로 변환 | NULL 전파 | nullptr 체크 필요 | null 전파 |
| **Numeric Precision** | widening 자동 | 자동 BigInt 없음 | number로 통합 | 명시적 필수 | DECIMAL 지정 | 명시적 | DecimalType |
| **Pitfall** | ClassCastException | "1" + 2 = "12" | `as any` 위험 | 없음 (엄격) | 암시적 NULL | reinterpret_cast 오용 | 스키마 불일치 |

### 2.2 Semantic Notes

#### JavaScript/TypeScript: Truthy/Falsy Coercion (Critical!)

JavaScript의 암시적 변환은 악명 높은 버그의 원인입니다:

```javascript
// == vs === (Coercion의 함정)
"5" == 5        // true  (암시적 변환)
"5" === 5       // false (타입 검사 포함)

0 == false      // true
0 === false     // false

null == undefined  // true
null === undefined // false

// Truthy/Falsy 값들
Boolean(0)          // false
Boolean("")         // false
Boolean(null)       // false
Boolean(undefined)  // false
Boolean(NaN)        // false
Boolean([])         // true  (빈 배열도 truthy!)
Boolean({})         // true  (빈 객체도 truthy!)

// + 연산자의 타입 변환
"5" + 3       // "53" (문자열 연결)
"5" - 3       // 2    (숫자 연산)
[] + []       // ""   (배열 → 문자열)
[] + {}       // "[object Object]"
{} + []       // 0 (블록 + 배열)
```

**TypeScript 타입 단언의 위험**:
```typescript
// as 키워드 - 컴파일러를 신뢰하게 함
const x = someValue as string;  // 런타임 체크 없음!

// Type Guard가 더 안전
function isString(x: unknown): x is string {
    return typeof x === "string";
}

// 위험한 패턴
const data = apiResponse as User;  // API가 실제로 User를 반환하는지 모름
```

#### Java: Primitive vs Object Casting

```java
// Primitive Widening (자동)
int i = 100;
long l = i;       // OK: int → long (widening)
double d = l;     // OK: long → double (widening)

// Primitive Narrowing (명시적 필요)
double d = 3.99;
int i = (int) d;  // i = 3 (소수점 손실!)

long big = 10_000_000_000L;
int small = (int) big;  // 오버플로우! 예상치 못한 값

// Object Casting
Object obj = "Hello";
String s = (String) obj;  // OK

Object num = 123;
String s = (String) num;  // ClassCastException!

// 안전한 캐스팅 패턴
if (obj instanceof String str) {  // Java 16+ Pattern Matching
    System.out.println(str.length());
}

// Auto-boxing/Unboxing (암시적)
Integer boxed = 100;      // int → Integer (boxing)
int primitive = boxed;     // Integer → int (unboxing)
Integer nullBox = null;
int crash = nullBox;       // NullPointerException!
```

#### Go: Strict No-Coercion Policy

Go는 의도적으로 암시적 변환을 허용하지 않습니다:

```go
// Go는 모든 변환이 명시적
var i int = 42
var f float64 = float64(i)  // 명시적 변환 필수
var u uint = uint(i)         // 명시적 변환 필수

// 이건 컴파일 에러
// var f float64 = i  // cannot use i (type int) as type float64

// 문자열 변환
import "strconv"
s := strconv.Itoa(42)        // int → string
n, err := strconv.Atoi("42") // string → int (에러 처리 필수)

// 인터페이스 타입 단언
var i interface{} = "hello"
s := i.(string)              // 실패시 panic
s, ok := i.(string)          // 안전한 패턴 (ok = false면 제로값)

// 타입 스위치
switch v := i.(type) {
case string:
    fmt.Println("string:", v)
case int:
    fmt.Println("int:", v)
}
```

#### SQL: CAST and Implicit Conversions

```sql
-- 명시적 CAST
SELECT CAST('123' AS INTEGER);           -- 123
SELECT CAST(3.14159 AS DECIMAL(5,2));    -- 3.14
SELECT CAST('2024-01-01' AS DATE);

-- 암시적 변환 (데이터베이스마다 다름)
SELECT '10' + 5;
-- PostgreSQL: 에러 (strict)
-- MySQL: 15 (암시적 변환)
-- SQL Server: 15 (암시적 변환)

-- 타입 호환성 매트릭스 (PostgreSQL 예시)
-- VARCHAR → INTEGER: CAST 필요
-- INTEGER → VARCHAR: 자동 (일부 문맥)
-- DATE → TIMESTAMP: 자동
-- TIMESTAMP → DATE: CAST 필요 (시간 손실)

-- NULL 처리
SELECT CAST(NULL AS INTEGER);  -- NULL (NULL은 전파됨)

-- 안전한 캐스팅 (SQL Server, PostgreSQL 14+)
SELECT TRY_CAST('abc' AS INTEGER);  -- NULL (에러 대신)

-- 숫자 정밀도
SELECT CAST(1234567890123 AS INTEGER);  -- 오버플로우 가능!
SELECT CAST(3.14159265359 AS DECIMAL(5,2));  -- 3.14 (반올림)
```

#### C++: Cast Varieties Explained

C++은 4가지 명시적 캐스트를 제공합니다:

```cpp
// 1. static_cast: 컴파일 타임 타입 변환 (가장 일반적)
double d = 3.14;
int i = static_cast<int>(d);  // d의 정수 부분 (3)

Base* b = new Derived();
Derived* d = static_cast<Derived*>(b);  // 업캐스트 (안전)

// 2. dynamic_cast: 런타임 타입 체크 (다형성 클래스용)
Base* b = getObject();
Derived* d = dynamic_cast<Derived*>(b);
if (d != nullptr) {  // 성공 여부 체크
    d->derivedMethod();
}

// 3. const_cast: const 속성 제거/추가
const int* p = &value;
int* modifiable = const_cast<int*>(p);  // const 제거 (위험!)

// 4. reinterpret_cast: 비트 패턴 재해석 (매우 위험)
int* p = new int(65);
char* c = reinterpret_cast<char*>(p);  // 메모리를 char로 해석

// 암시적 변환
int i = 10;
double d = i;      // OK: 암시적 widening
int* p = nullptr;  // OK: nullptr → int*

// 위험한 패턴
void* rawPtr = malloc(100);
MyClass* obj = reinterpret_cast<MyClass*>(rawPtr);  // 타입 안전성 없음
```

#### Spark: Column Type Casting

```python
# PySpark Column Casting
from pyspark.sql.functions import col
from pyspark.sql.types import IntegerType, StringType, DecimalType

df = spark.createDataFrame([("1", "2.5"), ("3", "4.7")], ["a", "b"])

# 명시적 캐스팅
df.select(
    col("a").cast(IntegerType()),      # "1" → 1
    col("b").cast("double"),           # "2.5" → 2.5
    col("b").cast(DecimalType(10, 2))  # 정밀도 지정
)

# 암시적 변환 (스키마 추론)
df = spark.read.csv("data.csv", inferSchema=True)
# inferSchema=True: 자동으로 타입 추론 (위험할 수 있음)
# inferSchema=False: 모두 StringType (안전하지만 변환 필요)

# 캐스팅 실패 시 NULL
df.select(col("a").cast("integer"))  # "abc" → NULL

# 날짜/시간 변환
from pyspark.sql.functions import to_date, to_timestamp
df.select(
    to_date(col("date_str"), "yyyy-MM-dd"),
    to_timestamp(col("ts_str"), "yyyy-MM-dd HH:mm:ss")
)
```

```scala
// Scala Spark
import org.apache.spark.sql.types._

df.select(
  $"a".cast(IntegerType),
  $"b".cast("double")
)

// Dataset 타입 변환
case class Person(name: String, age: Int)
val ds: Dataset[Person] = df.as[Person]  // DataFrame → Dataset
```

### 2.3 Numeric Precision Loss Examples

```
언어별 정밀도 손실 사례:

Java:
  double d = 0.1 + 0.2;
  // d = 0.30000000000000004 (부동소수점 오차)

  long big = 9_007_199_254_740_993L;
  double converted = big;
  // converted = 9007199254740992.0 (정밀도 손실!)

JavaScript:
  0.1 + 0.2 === 0.3  // false!
  0.1 + 0.2          // 0.30000000000000004

  Number.MAX_SAFE_INTEGER  // 9007199254740991
  9007199254740993 === 9007199254740992  // true (정밀도 손실)

Python:
  0.1 + 0.2  // 0.30000000000000004

  # Decimal 사용 권장 (금융 계산)
  from decimal import Decimal
  Decimal('0.1') + Decimal('0.2')  // Decimal('0.3')

SQL:
  SELECT 1.0 / 3.0;  -- 정밀도는 DB 설정에 따름
  SELECT CAST(1 AS DECIMAL(38,18)) / 3;  -- 고정밀도
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.5](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html) | Conversions and Contexts |
| Python | [Built-in Types](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex) | Numeric Type Conversions |
| TypeScript | [Type Assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions) | as, <Type> syntax |
| Go | [Conversions](https://go.dev/ref/spec#Conversions) | Explicit conversions only |
| SQL | [CAST Function](https://www.postgresql.org/docs/current/sql-expressions.html#SQL-SYNTAX-TYPE-CASTS) | PostgreSQL Type Casts |
| C++ | [Type Conversions](https://en.cppreference.com/w/cpp/language/expressions#Conversions) | static_cast, dynamic_cast, etc. |
| Spark | [Data Types](https://spark.apache.org/docs/latest/sql-ref-datatypes.html) | cast() function |

---

## 4. Palantir Context Hint

**Foundry/OSDK Relevance**:
- 데이터 파이프라인에서 스키마 변환 시 타입 캐스팅 필수
- TypeScript OSDK에서 API 응답 타입 단언 주의 (`as` 남용 금지)
- Python transforms에서 Decimal vs float 선택 (금융 데이터)
- Java 서비스에서 DTO 변환 시 ClassCastException 방지

**Interview Relevance**:
- "JavaScript에서 `==` vs `===` 차이는?"
  - `==`는 타입 강제 변환 후 비교, `===`는 타입까지 비교
- "Java에서 ClassCastException 방지 방법은?"
  - `instanceof` 체크 또는 Java 16+ Pattern Matching
- "타입 캐스팅의 위험성은?"
  - 정밀도 손실, 오버플로우, 런타임 예외
- "Go가 암시적 변환을 허용하지 않는 이유는?"
  - 명시성과 안전성 우선 설계 철학

---

## 5. Cross-References

### Related Concepts
- → F20_static_vs_dynamic_typing (타입 시스템 기초)
- → F21_type_inference (컴파일러의 타입 추론)
- → F03_constant_semantics (타입 고정과 불변성)
- → F23_null_safety (캐스팅 시 null 처리)

### Existing KB Links
- → 00e_typescript_intro (TypeScript 타입 단언)
- → 22_java_kotlin_backend_foundations (Java 타입 변환)
- → 10_sql_fundamentals (SQL CAST 함수)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
