# F03: Constant Semantics (상수 의미론)

> **Concept ID**: `F03_constant_semantics`
> **Universal Principle**: "변하지 않는 값"을 표현하는 방법과 그 실제 의미
> **Prerequisites**: F01_variable_binding, F02_mutability_patterns

---

## 1. Universal Concept (언어 무관 개념 정의)

**상수(Constant)**는 "변하지 않는다"는 의도를 코드로 표현합니다. 하지만 언어마다 "무엇이 변하지 않는가"가 다릅니다.

세 가지 층위:
1. **컴파일 타임 상수**: 컴파일 시 값이 결정됨 (C의 `#define`, Java의 `static final`)
2. **런타임 상수**: 한 번 초기화되면 변경 불가 (JavaScript의 `const`)
3. **깊은 불변성**: 객체 내부까지 모두 불변 (드묾)

**Mental Model**:
```
const x = {a: 1}
     │
     ▼
   x ────────→ { a: 1 }
   │(바인딩 고정)   │(내용 변경 가능!)
   ✗ x = ...      ✓ x.a = 2
```

**Why This Matters**:
- `const` ≠ 불변성이라는 사실을 모르면 버그 발생
- 진정한 불변성이 필요한 경우와 재바인딩 방지만 필요한 경우 구분 필요
- 컴파일 타임 상수는 성능 최적화에 활용됨

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Compile-time Const** | `static final` + primitive | None | `as const` | `const` (untyped) | 리터럴 | `constexpr` | 없음 |
| **Runtime Const** | `final` | 컨벤션 (ALL_CAPS) | `const` | 없음 | 없음 | `const` | `val` |
| **Deep Immutability** | 수동 구현 | `tuple`, `frozenset` | `Readonly<T>` | 없음 | N/A | `const &` | 기본 (RDD/DF) |
| **Const Object Mutation** | 가능 | N/A | 가능 | N/A | N/A | 가능 (mutable 멤버) | 불가능 |
| **Pitfall** | final 객체 내부 변경 | ALL_CAPS는 약속일 뿐 | const 객체 mutation | const는 숫자/문자열만 | 없음 | const_cast 오용 | 없음 |

### 2.2 Semantic Notes

**Compile-time Const**:
- **Java**: `static final int X = 10;` → 컴파일러가 인라인 가능
- **C++**: `constexpr int X = 10;` → 컴파일 타임에 평가 보장
- **Go**: `const Pi = 3.14` → untyped constant, 타입 추론됨
- **TypeScript**: `as const`로 리터럴 타입 고정

**Runtime Const**:
- **JavaScript/TS**: `const`는 TDZ(Temporal Dead Zone) + 재할당 금지
- **Java**: `final` 지역 변수는 한 번만 할당 가능
- **Python**: 컨벤션만 존재 (`ALL_CAPS`)

**Deep Immutability**:
- TypeScript: `Readonly<T>`, `ReadonlyArray<T>` 타입 레벨 보호
- JavaScript: `Object.freeze()` 런타임 보호 (얕음)
- Python: `tuple`, `frozenset` 내장 불변 타입

**Const Object Mutation 예시**:
```typescript
const user = { name: "Kim" };
user.name = "Lee";  // ✓ 허용됨!
user = { name: "Park" };  // ✗ 에러: 재할당 불가
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS 4.12.4](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.12.4) | final Variables |
| Python | [PEP 8](https://peps.python.org/pep-0008/#constants) | Constants naming |
| TypeScript | [const assertions](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-4.html#const-assertions) | as const |
| Go | [Constants](https://go.dev/ref/spec#Constants) | Constant declarations |
| SQL | N/A | 상수는 리터럴로 표현 |
| C++ | [constexpr](https://en.cppreference.com/w/cpp/language/constexpr) | Constant expressions |
| Spark | [Immutability](https://spark.apache.org/docs/latest/rdd-programming-guide.html) | RDD immutability |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- TypeScript OSDK: `const`로 선언해도 객체 프로퍼티 변경 가능
- 상수 설정값은 `as const`로 리터럴 타입 사용 권장
- Java 서비스: `static final` 상수는 configuration 용도

**Interview Relevance**:
- "const와 Object.freeze의 차이는?"
- "왜 Java는 const 키워드가 없나요?" (reserved word지만 미사용)
- "컴파일 타임 상수의 이점은?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F01_variable_binding (상수 = 바인딩 고정)
- → F02_mutability_patterns (상수 ≠ 불변성)
- → F20_static_vs_dynamic_typing (컴파일 타임 vs 런타임)

### Existing KB Links
- → 00e_typescript_intro (const, let, var)
- → 22_java_kotlin_backend_foundations (final, val)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
