# F02: Mutability Patterns (가변성 패턴)

> **Concept ID**: `F02_mutability_patterns`
> **Universal Principle**: 바인딩된 값을 변경할 수 있는지, 어떻게 변경하는지의 규칙
> **Prerequisites**: F01_variable_binding

---

## 1. Universal Concept (언어 무관 개념 정의)

**가변성(Mutability)**은 "값이 생성된 후 변경될 수 있는가?"에 대한 답입니다.

두 가지 층위가 있습니다:
1. **바인딩 가변성**: 변수가 다른 값을 가리킬 수 있는가? (rebinding)
2. **값 가변성**: 값 자체의 내부 상태를 바꿀 수 있는가? (mutation)

**Mental Model**:
- **Rebinding**: 이름표를 떼서 다른 물건에 붙이기
- **Mutation**: 물건 자체를 변형하기 (페인트칠, 부품 교체)

```
Rebinding:   x ──→ "hello"     x ──→ "world"   (x가 다른 것을 가리킴)
Mutation:    x ──→ [1,2,3]     x ──→ [1,2,3,4] (같은 리스트에 추가)
```

**Why This Matters**:
- 불변성(Immutability)은 **버그 감소**, **동시성 안전**, **추론 용이성**을 제공
- 가변성은 **성능 최적화**, **메모리 효율**에 필요
- 언어마다 기본값이 다름: Rust는 불변 기본, Python은 가변 기본

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Immutable by Default** | No | No | No | No | Yes (SELECT) | No | Yes (RDD/DF) |
| **Immutable Keyword** | `final` (binding only) | None (convention) | `const` (binding only) | None | N/A | `const` | `val` |
| **Truly Immutable Types** | String, wrapper | tuple, frozenset, str | readonly, as const | string (내부적) | All values | const 참조 | RDD, DataFrame |
| **Defensive Copy** | 수동 | 수동 (copy, deepcopy) | spread, Object.freeze | 자동 (값 전달) | 자동 | 수동 | 자동 (transformation) |
| **Pitfall** | final ≠ deep immutable | mutable default args | const obj mutation | slice 참조 공유 | UPDATE의 부수효과 | const_cast 남용 | cache 미사용 시 재계산 |

### 2.2 Semantic Notes

**Immutable by Default**:
- **Rust** (비교용): 모든 변수가 기본 불변, `mut` 명시 필요
- **Spark**: RDD/DataFrame은 불변. transformation은 새 객체 생성
- **SQL**: SELECT 결과는 불변. UPDATE만 mutation

**Immutable Keyword**:
- Java `final`, TS `const`, Go 없음 → **재바인딩만 금지**, 값은 변경 가능
- Python: 진정한 immutable 키워드 없음. `tuple`로 불변 컬렉션 사용

**Truly Immutable Types**:
- **Java**: `String`은 진정한 불변. `StringBuilder`는 가변 대안
- **Python**: `str`, `int`, `tuple`, `frozenset`은 불변
- **JavaScript/TS**: primitive만 불변, 객체는 모두 가변

**Defensive Copy**:
- 가변 객체를 외부에 노출할 때 복사본 반환
- Java: `Collections.unmodifiableList()` (읽기 전용 뷰)
- Python: `copy.deepcopy()` (깊은 복사)

**Common Pitfalls**:
- `const list = [1,2,3]; list.push(4);` ← TypeScript에서 합법!
- `final List<String> x = new ArrayList<>(); x.add("a");` ← Java에서 합법!
- Python mutable default: `def f(x=[]): x.append(1); return x`

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.4.12.4](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.12.4) | final Variables |
| Python | [Data Model](https://docs.python.org/3/reference/datamodel.html#objects-values-and-types) | Mutable vs Immutable |
| TypeScript | [Type Inference](https://www.typescriptlang.org/docs/handbook/type-inference.html) | const assertions |
| Go | [FAQ](https://go.dev/doc/faq#no_const_structs) | Why no immutable? |
| SQL | [ACID](https://en.wikipedia.org/wiki/ACID) | Isolation and consistency |
| C++ | [const correctness](https://isocpp.org/wiki/faq/const-correctness) | Const member functions |
| Spark | [RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html) | Immutable RDDs |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- Foundry DataFrame은 불변 (Spark 기반)
- OSDK 객체는 참조로 전달됨 → 의도치 않은 mutation 주의
- Actions에서 입력 객체 직접 수정 금지 (새 객체 반환)

**Interview Relevance**:
- "왜 String을 불변으로 설계했을까요?"
- "가변 상태가 동시성에서 문제가 되는 이유는?"
- "defensive copy가 언제 필요한가요?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F01_variable_binding (바인딩 vs 값 변경)
- → F03_constant_semantics (const/final의 진짜 의미)
- → F33_thread_safety (불변성과 동시성)
- → F35_ownership_borrowing (Rust의 소유권 모델)

### Existing KB Links
- → 00a_programming_fundamentals (기초 개념)
- → 21_python_backend_async (Python 비동기와 상태)
- → 13_pipeline_builder (Spark 불변 변환)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
