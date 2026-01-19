# F12: Block vs Function Scope (블록 스코프 vs 함수 스코프)

> **Concept ID**: `F12_block_vs_function_scope`
> **Universal Principle**: 변수의 유효 범위가 블록({}) 단위인지 함수 단위인지의 차이
> **Prerequisites**: F10_lexical_scope (렉시컬 스코프)

---

## 1. Universal Concept (언어 무관 개념 정의)

**블록 스코프 vs 함수 스코프**는 변수가 어디까지 유효한지를 결정하는 두 가지 핵심 규칙입니다.

- **블록 스코프 (Block Scope)**: 변수가 선언된 `{}` 블록 내에서만 유효합니다. `if`, `for`, `while` 등의 블록을 벗어나면 접근 불가능합니다.
- **함수 스코프 (Function Scope)**: 변수가 선언된 함수 전체에서 유효합니다. 함수 내부 어디서든 접근 가능합니다.

대부분의 현대 언어는 블록 스코프를 기본으로 채택했지만, JavaScript의 `var`와 Python은 여전히 함수 스코프를 따릅니다.

**Mental Model**:
```
// Block Scope (let/const in JS, Java, Go, C++)
if (true) {
    let x = 10;  // 이 블록에서만 유효
}
// x는 여기서 접근 불가 → ReferenceError

// Function Scope (var in JS, Python)
if True:
    x = 10  # Python: 함수 전체에서 유효
# x는 여기서도 접근 가능! → 10
```

**Why This Matters**:
스코프 규칙을 모르면:
- JavaScript에서 `var`로 선언한 루프 변수가 클로저에서 예상과 다르게 동작
- Python에서 `for` 루프 변수가 루프 밖에서 살아있어 버그 발생
- 다른 언어에서 경험을 가져올 때 혼란

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Default Scope** | Block | Function | Block (let/const) | Block | Statement/Block | Block | Block (val/var) |
| **Block `{}` Creates Scope** | Yes | No | Yes (let/const) | Yes | Yes | Yes | Yes |
| **`for` Loop Variable** | Block scoped | Function scoped | Block (let) / Function (var) | Block scoped | Cursor scoped | Block scoped | Block scoped |
| **`if/else` Variable** | Block scoped | Function scoped | Block (let) / Function (var) | Block scoped | Block scoped | Block scoped | Block scoped |
| **Major Pitfall** | 중첩 블록 혼란 | 루프 변수 누출 | var 호이스팅 | 짧은 선언 섀도잉 | 트랜잭션 스코프 | RAII 타이밍 | closure 캡처 |

### 2.2 Semantic Notes

**Default Scope**:
- **Java, Go, C++, TypeScript (let/const)**: 블록 스코프가 기본. `{}`를 만나면 새로운 스코프 생성
- **Python**: 함수 스코프가 기본. `if`, `for`, `while` 내부 변수도 함수 전체에서 접근 가능
- **TypeScript (var)**: JavaScript 호환성으로 함수 스코프 유지

**Block `{}` Creates Scope**:
- **블록 스코프 언어**: 중괄호가 새로운 스코프 경계를 형성
- **Python**: 중괄호 대신 들여쓰기 사용, 하지만 새로운 스코프를 만들지 않음
- **SQL**: BEGIN...END 또는 특정 구문(CASE, 서브쿼리)에서 스코프 생성

**`for` Loop Variable**:
- **Java, Go, C++**: 루프 변수는 루프 블록 내에서만 유효
- **Python**: 루프 변수는 루프 종료 후에도 마지막 값 유지 (의도치 않은 동작 원인)
- **TypeScript**: `let`은 매 반복마다 새 바인딩, `var`는 하나의 바인딩 공유

**`if/else` Variable**:
- **대부분 언어**: 조건문 블록 내에서만 유효
- **Python**: 조건문 내 변수가 함수 전체에서 접근 가능

**Common Pitfalls**:
- **JavaScript (var)**: 클로저와 함수 스코프의 조합으로 루프에서 예상치 못한 동작
- **Python**: `for i in range(3): pass` 후 `i`가 여전히 2
- **Go**: `:=`로 같은 이름 재선언 시 실수로 섀도잉

### 2.3 Critical Comparison: Loop Variable Scope

| Language | `for` Loop Variable | `if` Block Variable | Closure Behavior |
|----------|---------------------|---------------------|------------------|
| JavaScript (let) | Block scoped | Block scoped | 매 반복 새 바인딩 |
| JavaScript (var) | Function scoped | Function scoped | 하나의 바인딩 공유 |
| Python | Function scoped | Function scoped | 마지막 값만 캡처 |
| Java | Block scoped | Block scoped | effectively final 필요 |
| Go | Block scoped | Block scoped | 매 반복 새 바인딩 (Go 1.22+) |
| C++ | Block scoped | Block scoped | 값/참조 캡처 선택 |
| Spark (Scala) | Block scoped | Block scoped | 직렬화 주의 |

### 2.4 Classic Interview Example: Closure in Loop

```javascript
// JavaScript var (함수 스코프) - 잘못된 예
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// 출력: 3, 3, 3 (모든 클로저가 같은 i를 참조)

// JavaScript let (블록 스코프) - 올바른 예
for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// 출력: 0, 1, 2 (매 반복 새로운 i 바인딩)
```

```python
# Python (함수 스코프) - 주의 필요
funcs = []
for i in range(3):
    funcs.append(lambda: print(i))
for f in funcs:
    f()
# 출력: 2, 2, 2 (모든 lambda가 같은 i를 참조)

# Python 해결책: 기본값 인자로 캡처
funcs = []
for i in range(3):
    funcs.append(lambda x=i: print(x))
for f in funcs:
    f()
# 출력: 0, 1, 2
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.6](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) | Scope of a Declaration |
| Python | [Execution Model](https://docs.python.org/3/reference/executionmodel.html) | Naming and binding |
| TypeScript | [Variable Declarations](https://www.typescriptlang.org/docs/handbook/variable-declarations.html) | let vs var scoping |
| Go | [Declarations and scope](https://go.dev/ref/spec#Declarations_and_scope) | Block scope rules |
| SQL | [ISO SQL](https://www.iso.org/standard/63555.html) | Scope of declarations (vendor-specific) |
| C++ | [cppreference Scope](https://en.cppreference.com/w/cpp/language/scope) | Block scope |
| Spark | [Scala Language Spec](https://scala-lang.org/files/archive/spec/2.13/) | Blocks and scoping |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- TypeScript OSDK에서 `let`/`const` 사용 권장 (블록 스코프의 예측 가능성)
- Python transforms에서 루프 변수 누출 주의 필요
- Go 서비스에서 고루틴과 스코프 상호작용 이해 필수

**Interview Relevance**:
- "JavaScript에서 `var`와 `let`의 스코프 차이를 설명하세요"
- "Python에서 for 루프 변수가 루프 밖에서 접근 가능한 이유는?"
- "이 코드의 출력은 무엇일까요? (클로저 + 루프 문제)"
- "Go에서 `for` 루프와 고루틴을 함께 쓸 때 주의할 점은?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F10_lexical_scope (렉시컬 스코프 규칙)
- → F13_hoisting (var의 호이스팅과 TDZ)
- → F05_shadowing (블록 내 변수 섀도잉)
- → F11_closure_capture (클로저의 변수 캡처)
- → F01_variable_binding (바인딩의 기초)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00e_typescript_intro (TypeScript의 let/const/var)
- → 00d_golang_intro (Go의 블록 스코프)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
