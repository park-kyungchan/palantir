# F05: Variable Shadowing (변수 섀도잉)

> **Concept ID**: `F05_shadowing`
> **Universal Principle**: 내부 스코프에서 외부 스코프의 동일 이름 변수를 "가리는" 현상
> **Prerequisites**: F01_variable_binding, F10_lexical_scope

---

## 1. Universal Concept (언어 무관 개념 정의)

**섀도잉(Shadowing)**은 내부 스코프에서 외부 스코프와 동일한 이름의 변수를 선언할 때 발생합니다. 내부 변수가 외부 변수를 "가려서" 보이지 않게 만듭니다.

**Mental Model**:
```
외부 스코프: x = 10
                │
내부 스코프: x = 20  ← 외부의 x를 "가림" (shadow)
                │
           print(x) → 20 (내부 x만 보임)
```

**Shadowing vs Reassignment**:
- **섀도잉**: 새로운 변수를 생성 (외부 변수는 그대로 존재)
- **재할당**: 기존 변수의 값을 변경 (같은 변수)

```
# Shadowing (Rust)
let x = 5;
let x = x + 1;  // 새로운 x, 이전 x는 가려짐

# Reassignment (Python)
x = 5
x = x + 1  // 같은 x, 값만 변경
```

**Why This Matters**:
- 의도치 않은 섀도잉은 디버깅하기 어려운 버그 유발
- 일부 언어(Rust)는 섀도잉을 권장 (타입 변환에 유용)
- 일부 언어(Java)는 특정 상황에서 섀도잉 금지
- 린터(linter)가 섀도잉 경고를 주는 이유 이해 필요

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Local Shadowing** | 허용 | 허용 | 허용 | 허용 (`:=` 주의) | CTE 허용 | 허용 | 허용 (DataFrame) |
| **Parameter Shadowing** | 금지 | 허용 | 허용 | 허용 | N/A | 허용 | N/A |
| **Field Shadowing** | 허용 (this 필요) | 허용 (self 필요) | 허용 (this 필요) | 없음 (구조체) | N/A | 허용 | N/A |
| **Intentional Use** | 드묾 | 드묾 | 드묾 | 드묾 | CTE 체이닝 | 드묾 | 변환 체이닝 |
| **Pitfall** | this.field 누락 | 클로저 캡처 | let/const 혼동 | := vs = 혼동 | 서브쿼리 별칭 | 포인터 섀도잉 | 지연 평가 오해 |

### 2.2 Semantic Notes

**Local Shadowing**:
- **Java**: 블록 내 섀도잉 허용, 같은 블록 내 중복 선언 금지
- **Python**: 함수 내 어디서든 같은 이름 재사용 가능 (실제로는 재할당)
- **Rust** (비교): 의도적 섀도잉 권장 - 타입 변환 시 유용
- **Go**: `:=`로 실수로 섀도잉하기 쉬움

**Parameter Shadowing**:
```java
// Java - 금지
void method(int x) {
    int x = 10;  // 컴파일 에러!
}

// Python - 허용 (하지만 안티패턴)
def method(x):
    x = 10  # 허용되지만 혼란 유발
```

**Field Shadowing**:
```java
class Example {
    int value = 10;
    void method(int value) {  // 파라미터가 필드를 섀도잉
        this.value = value;   // this로 필드 접근
    }
}
```

**Go의 := 함정**:
```go
x := 10
if true {
    x := 20  // 새로운 x! (섀도잉)
    // 외부 x는 여전히 10
}
// x는 10
```

**SQL CTE 체이닝**:
```sql
WITH data AS (SELECT * FROM raw),
     data AS (SELECT * FROM data WHERE active)  -- 이전 data를 섀도잉
SELECT * FROM data;
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS 6.4](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html#jls-6.4) | Shadowing and Obscuring |
| Python | [Execution Model](https://docs.python.org/3/reference/executionmodel.html) | Resolution of names |
| TypeScript | [Variable Declarations](https://www.typescriptlang.org/docs/handbook/variable-declarations.html) | Block-scoping |
| Go | [Declarations and scope](https://go.dev/ref/spec#Declarations_and_scope) | Scope rules |
| SQL | [CTE](https://www.postgresql.org/docs/current/queries-with.html) | WITH Queries |
| C++ | [Scope](https://en.cppreference.com/w/cpp/language/scope) | Name hiding |
| Spark | [DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html) | Column references |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- TypeScript OSDK에서 변수명 충돌 주의
- Python transforms에서 DataFrame 변수 재사용 시 섀도잉 vs 변환 구분
- Java 서비스에서 필드/파라미터 섀도잉 패턴 (this 사용)

**Interview Relevance**:
- "이 코드에서 버그를 찾으세요" (섀도잉 관련)
- "Go에서 :=와 =의 차이로 인한 문제는?"
- "클로저에서 변수 캡처 시 섀도잉 문제는?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F01_variable_binding (섀도잉 = 새 바인딩 생성)
- → F10_lexical_scope (섀도잉의 전제 조건)
- → F11_closure_capture (클로저와 섀도잉 상호작용)
- → F13_hoisting (호이스팅과 섀도잉)

### Existing KB Links
- → 00e_typescript_intro (let/const와 섀도잉)
- → 21_python_backend_async (클로저 캡처 문제)
- → 22_java_kotlin_backend_foundations (this 키워드)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
