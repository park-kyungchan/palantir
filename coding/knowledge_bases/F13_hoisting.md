# F13: Hoisting (호이스팅)

> **Concept ID**: `F13_hoisting`
> **Universal Principle**: 선언이 스코프 최상단으로 "끌어올려지는" 것처럼 동작하는 현상
> **Prerequisites**: F10_lexical_scope, F12_block_vs_function_scope

---

## 1. Universal Concept (언어 무관 개념 정의)

**호이스팅(Hoisting)**은 코드 실행 전에 선언(declaration)이 해당 스코프의 최상단으로 이동한 것처럼 처리되는 동작을 말합니다. 이 개념은 주로 JavaScript에서 유명하지만, 다른 언어에서도 유사한 동작이 존재합니다.

호이스팅이 발생하면:
- 변수나 함수를 선언하기 전에 참조할 수 있음 (일부 언어)
- 초기화(initialization)는 호이스팅되지 않음 — 선언만 끌어올려짐
- TDZ(Temporal Dead Zone)가 있는 경우, 선언 전 접근 시 에러 발생

**Mental Model**:
```javascript
// 여러분이 작성한 코드
console.log(x);  // undefined (에러 아님!)
var x = 10;

// JavaScript 엔진이 해석하는 방식
var x;           // 선언이 "hoisted" (끌어올려짐)
console.log(x);  // undefined
x = 10;          // 할당은 원래 위치에

// let의 경우 (TDZ 존재)
console.log(y);  // ReferenceError!
let y = 10;      // TDZ: 선언 전 접근 금지
```

**Why This Matters**:
호이스팅을 이해하지 못하면:
- JavaScript에서 `undefined` vs `ReferenceError` 차이를 모름
- 왜 함수 선언은 어디서든 호출 가능한지 혼란
- `var` vs `let`/`const` 선택의 근거를 모름
- 다른 언어에서 "선언 전 사용 불가" 규칙이 더 안전한 이유를 이해 못함

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Variable Hoisting** | None (컴파일 에러) | None (NameError) | var: Yes / let,const: TDZ | None (컴파일 에러) | N/A (선언적) | None (컴파일 에러) | None (선언적) |
| **Function Hoisting** | None (순서 무관) | None (정의 후 호출) | 선언: Yes / 표현식: No | None (순서 무관) | N/A | 선언/정의 분리 | N/A |
| **TDZ Behavior** | N/A (선언 필수) | N/A (선언 없음) | let/const에 적용 | N/A | N/A | N/A | N/A |
| **Class Hoisting** | None | None | TDZ 적용 | None | N/A | 전방 선언 필요 | N/A |
| **Pitfall** | 컴파일러가 잡음 | NameError 런타임 | undefined vs ReferenceError | 컴파일러가 잡음 | - | 전방 선언 누락 | - |

### 2.2 Semantic Notes

**Variable Hoisting**:
- **JavaScript/TypeScript (var)**: 선언이 함수 스코프 최상단으로 호이스팅, 값은 `undefined`
- **JavaScript/TypeScript (let/const)**: 호이스팅되지만 TDZ로 인해 선언 전 접근 시 ReferenceError
- **Python**: 호이스팅 없음. 할당 전 변수 접근 시 `NameError`
- **Java/Go/C++**: 정적 타입 언어로 선언 전 사용은 컴파일 에러

**Function Hoisting**:
- **JavaScript**: 함수 선언문(function declaration)은 전체가 호이스팅됨
  ```javascript
  sayHi();  // 작동함!
  function sayHi() { console.log("Hi"); }
  ```
- **JavaScript 함수 표현식**: 변수 규칙 따름 (var: undefined, let/const: TDZ)
  ```javascript
  sayHi();  // TypeError: sayHi is not a function
  var sayHi = function() { console.log("Hi"); };
  ```
- **Python**: 함수 정의 전 호출 시 `NameError`

**TDZ (Temporal Dead Zone)**:
- `let`과 `const`는 블록 시작부터 선언 위치까지 TDZ에 존재
- TDZ 내 접근 시 `ReferenceError` (var의 `undefined`보다 안전)
- 이유: 선언 전 접근은 거의 버그이므로 명시적 에러가 더 나음

**Class Hoisting**:
- **JavaScript/TypeScript**: 클래스 선언은 TDZ 적용 (함수 선언과 다름)
  ```javascript
  new MyClass();  // ReferenceError!
  class MyClass {}
  ```
- **C++**: 전방 선언(forward declaration) 필요
  ```cpp
  class B;  // 전방 선언
  class A { B* b; };  // B를 포인터로만 사용 가능
  class B { A* a; };
  ```

**Common Pitfalls**:
- **JavaScript var**: 의도치 않은 `undefined` 사용으로 버그
- **TypeScript**: strict 모드 없이 var 사용 시 호이스팅 문제 유지
- **Python**: 전역 변수 shadowing으로 인한 `UnboundLocalError`
  ```python
  x = 10
  def f():
      print(x)  # UnboundLocalError! (아래 할당 때문)
      x = 20
  ```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.6](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) | Scope of a Declaration |
| Python | [Execution Model](https://docs.python.org/3/reference/executionmodel.html) | Naming and Binding |
| TypeScript | [Variable Declarations](https://www.typescriptlang.org/docs/handbook/variable-declarations.html) | var, let, const differences |
| Go | [Declarations and Scope](https://go.dev/ref/spec#Declarations_and_scope) | Scope rules |
| SQL | [ISO SQL](https://www.iso.org/standard/63555.html) | Declarative semantics |
| C++ | [cppreference: Scope](https://en.cppreference.com/w/cpp/language/scope) | Declaration order |
| Spark | [Spark SQL](https://spark.apache.org/docs/latest/sql-ref.html) | Declarative SQL |

**JavaScript 핵심 자료**:
- [MDN: Hoisting](https://developer.mozilla.org/en-US/docs/Glossary/Hoisting)
- [ES6 TDZ Explained](https://www.jsv9000.app/) (시각화 도구)

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- TypeScript OSDK에서 `const`/`let` 사용 권장 (var 금지)
- Python transforms에서 전역 변수 shadowing 주의
- ESLint/Ruff 규칙으로 호이스팅 관련 문제 방지

**Interview Relevance**:
- "JavaScript에서 var와 let의 차이를 설명하세요"
- "TDZ(Temporal Dead Zone)가 무엇인가요?"
- "왜 let/const가 var보다 선호되나요?"
- "다음 코드의 출력은 무엇인가요?"
  ```javascript
  console.log(a);
  var a = 1;
  console.log(b);
  let b = 2;
  ```
  답: `undefined`, 그 다음 `ReferenceError`

**면접 함정 문제**:
```javascript
// 문제: 출력은?
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
// 답: 3, 3, 3 (var는 함수 스코프, 클로저가 같은 i 참조)

// let으로 수정하면?
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
// 답: 0, 1, 2 (let은 블록 스코프, 각 반복마다 새 i)
```

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F12_block_vs_function_scope (스코프 종류와 호이스팅의 관계)
- → F04_declaration_vs_definition (선언과 정의/초기화의 차이)
- → F01_variable_binding (바인딩 시점과 호이스팅)
- → F10_lexical_scope (렉시컬 스코프에서의 호이스팅)
- → F11_closure_capture (클로저와 var 호이스팅 문제)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00e_typescript_intro (TypeScript let/const 권장)
- → 03_javascript_typescript_intro (JavaScript 핵심)

---

## Appendix: Language-Specific Details

### JavaScript/TypeScript Hoisting Deep Dive

```javascript
// === var 호이스팅 ===
console.log(x);  // undefined
var x = 5;
console.log(x);  // 5

// 엔진 해석:
// var x;          <- 호이스팅됨
// console.log(x); <- undefined
// x = 5;
// console.log(x); <- 5

// === let/const TDZ ===
// console.log(y);  // ReferenceError: Cannot access 'y' before initialization
let y = 10;

// === 함수 선언 vs 표현식 ===
foo();  // "Hello" - 함수 선언은 전체 호이스팅
// bar();  // TypeError: bar is not a function
// baz();  // ReferenceError: Cannot access 'baz' before initialization

function foo() { console.log("Hello"); }
var bar = function() { console.log("World"); };
const baz = () => console.log("Arrow");

// === 클래스는 TDZ ===
// const instance = new MyClass();  // ReferenceError
class MyClass {
  constructor() { this.value = 42; }
}
```

### Python: No Hoisting, But Watch for Shadowing

```python
# Python에는 호이스팅이 없음
# print(x)  # NameError: name 'x' is not defined
x = 10

# 하지만 함수 내 전역 변수 shadowing 주의!
y = 100
def tricky():
    # Python은 함수 전체를 분석하여 y가 로컬임을 결정
    # print(y)  # UnboundLocalError!
    y = 200  # 이 할당 때문에 y는 로컬 변수로 취급
    print(y)

# 해결책: global 키워드 사용
def fixed():
    global y
    print(y)  # 100
    y = 200
```

### Go/Java/C++: Compile-Time Safety

```go
// Go: 선언 전 사용은 컴파일 에러
func main() {
    // fmt.Println(x)  // undefined: x
    x := 10
    fmt.Println(x)
}
```

```java
// Java: 선언 전 사용은 컴파일 에러
public class Main {
    public static void main(String[] args) {
        // System.out.println(x);  // cannot find symbol
        int x = 10;
        System.out.println(x);
    }
}
```

```cpp
// C++: 선언 전 사용은 컴파일 에러
// 하지만 전방 선언(forward declaration)은 허용
class B;  // 전방 선언

class A {
    B* b;  // 포인터로는 사용 가능
    // B obj;  // 에러: incomplete type
};

class B {
    A* a;
};
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
