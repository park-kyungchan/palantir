# F04: Declaration vs Definition (선언과 정의)

> **Concept ID**: `F04_declaration_vs_definition`
> **Universal Principle**: "이런 것이 있다"(선언)와 "이것이 실제 내용이다"(정의)의 구분
> **Prerequisites**: F01_variable_binding

---

## 1. Universal Concept (언어 무관 개념 정의)

**선언(Declaration)**과 **정의(Definition)**는 다른 개념입니다:

- **선언**: 컴파일러/인터프리터에게 "이 이름이 존재하고, 이런 타입이다"라고 알림
- **정의**: 실제 메모리를 할당하고 값을 설정

**Mental Model**:
```
선언 = 계약서 (이름과 타입만 명시)
정의 = 실제 물건 제작 (메모리 할당, 값 할당)
```

**Why This Matters**:
- C/C++에서는 선언과 정의가 분리 가능 (헤더 파일 vs 소스 파일)
- Java/Python에서는 거의 항상 선언 = 정의
- TypeScript에서 `.d.ts` 파일은 선언만 담음
- 이 구분을 이해해야 링크 에러, 타입 에러를 해결할 수 있음

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **분리 가능** | interface만 | No | .d.ts 파일 | Yes (일부) | CREATE vs INSERT | Yes (헤더) | No |
| **Forward Declaration** | interface | 없음 | declare | 없음 | 없음 | 헤더 선언 | 없음 |
| **Implicit Definition** | 클래스 로드 시 | 할당 시 | 선언 시 | 패키지 로드 시 | DDL 실행 시 | 링크 시 | 평가 시 |
| **Type-only Declaration** | interface, abstract | typing.Protocol | type, interface | interface | CREATE TYPE | 클래스 전방 선언 | 스키마 정의 |
| **Pitfall** | 인터페이스 구현 누락 | NameError | 런타임 타입 체크 불가 | 순환 import | 스키마 불일치 | 링크 에러 | 스키마 추론 오류 |

### 2.2 Semantic Notes

**분리 가능**:
- **C++**: 헤더(.h)에 선언, 소스(.cpp)에 정의. 링커가 연결
- **TypeScript**: `.d.ts`는 타입 선언만. 실제 구현은 JS
- **Java**: `interface`는 계약 선언, `class`가 구현 정의

**Forward Declaration**:
- C++: `class Foo;` → "Foo라는 클래스가 있다"만 알림
- TypeScript: `declare function foo(): void;` → 외부 함수 존재 선언
- 순환 의존성 해결에 사용

**Implicit Definition**:
- **Python**: 할당 자체가 선언+정의. `x = 5`로 x 탄생
- **Java**: 클래스 로드 시 static 필드 정의
- **Go**: 패키지 import 시 init() 실행

**Type-only Declaration**:
```typescript
// 선언만 (구현 없음)
interface User {
  name: string;
  age: number;
}

// 정의 (실제 객체)
const user: User = { name: "Kim", age: 25 };
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS 6.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) | Declarations |
| Python | [Execution Model](https://docs.python.org/3/reference/executionmodel.html) | Binding of names |
| TypeScript | [Declaration Files](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html) | .d.ts files |
| Go | [Declarations](https://go.dev/ref/spec#Declarations_and_scope) | Declaration and scope |
| SQL | [CREATE vs INSERT](https://www.w3schools.com/sql/sql_create_table.asp) | DDL vs DML |
| C++ | [Declarations](https://en.cppreference.com/w/cpp/language/declarations) | Declaration vs definition |
| Spark | [Schema](https://spark.apache.org/docs/latest/sql-ref-datatypes.html) | Schema definition |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- Ontology 정의 = 타입 선언 (스키마)
- 실제 데이터 = 정의 (인스턴스)
- TypeScript OSDK의 `.d.ts` 생성 과정 이해 필요

**Interview Relevance**:
- "C++에서 선언과 정의의 차이는?"
- "왜 TypeScript는 .d.ts 파일이 필요한가?"
- "Python에서 NameError는 언제 발생하나?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F01_variable_binding (선언과 바인딩)
- → F10_lexical_scope (선언의 유효 범위)
- → F13_hoisting (선언의 호이스팅)
- → F72_interfaces_protocols (인터페이스 = 순수 선언)

### Existing KB Links
- → 00e_typescript_intro (TypeScript 선언)
- → 00a_programming_fundamentals (기초 개념)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
