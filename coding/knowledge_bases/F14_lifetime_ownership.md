# F14: Lifetime & Ownership (수명과 소유권)

> **Concept ID**: `F14_lifetime_ownership`
> **Universal Principle**: 변수/메모리가 유효한 기간과 소유권 관리 방식
> **Prerequisites**: F01_variable_binding, F10_lexical_scope

---

## 1. Universal Concept (언어 무관 개념 정의)

**수명(Lifetime)**은 변수나 메모리가 유효하게 접근 가능한 기간을 의미합니다. **소유권(Ownership)**은 해당 메모리를 해제할 책임이 누구에게 있는지를 결정합니다.

모든 프로그램은 메모리를 사용하고, 결국 그 메모리를 해제해야 합니다. 이 과정을 어떻게 관리하느냐에 따라 언어의 특성이 결정됩니다:
- **수동 관리 (C/C++)**: 프로그래머가 직접 할당(malloc/new)과 해제(free/delete)
- **자동 관리 (Java/Python/Go)**: 가비지 컬렉터(GC)가 더 이상 참조되지 않는 메모리 자동 회수
- **소유권 기반 (Rust)**: 컴파일 타임에 소유권 규칙으로 메모리 안전성 보장

**Mental Model**:
```
┌─────────────────────────────────────────┐
│ Memory Management Spectrum              │
├─────────────────────────────────────────┤
│                                         │
│  Manual ◄─────────────────────► Auto    │
│                                         │
│  C/C++     Rust      Java/Python/Go     │
│  (malloc)  (owner)   (GC)               │
│                                         │
│  위험하지만   안전하고    안전하지만        │
│  빠름       빠름       오버헤드 있음      │
└─────────────────────────────────────────┘
```

**Why This Matters**:
수명과 소유권을 이해하지 못하면:
- 메모리 누수(memory leak): 더 이상 필요 없는 메모리를 해제하지 않음
- 댕글링 포인터(dangling pointer): 이미 해제된 메모리를 참조
- Use-after-free: 해제된 메모리 사용으로 인한 보안 취약점
- GC 일시정지(GC pause): 언제 GC가 동작할지 예측 불가로 인한 성능 이슈

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Memory Management** | GC (G1/ZGC) | GC + Reference Counting | GC (V8 엔진) | GC (Concurrent) | DB 엔진 관리 | Manual / Smart Ptr | Executor 분산 관리 |
| **Lifetime Scope** | 참조 없으면 수집 대상 | 참조 카운트 0이면 즉시 해제 | 참조 없으면 수집 대상 | Escape Analysis로 결정 | 트랜잭션/세션 범위 | 스코프 종료 시 소멸 | Stage 완료 시 해제 |
| **Ownership Model** | 공유 참조 (no owner) | 공유 참조 (no owner) | 공유 참조 (no owner) | 공유 참조 (no owner) | N/A (선언적) | 명시적 소유권 가능 | Driver ↔ Executor |
| **Reference Type** | Strong/Weak/Soft/Phantom | Strong/Weak | Strong/Weak | Strong only | N/A | Raw/Unique/Shared | Broadcast/Accumulator |
| **Common Pitfall** | static 참조로 누수 | 순환 참조 | 클로저 메모리 누수 | 없음 (Escape Analysis) | 커서 미해제 | dangling pointer | Shuffle 메모리 폭발 |

### 2.2 Semantic Notes

**Memory Management**:
- **Java**: G1 GC(기본), ZGC(저지연), 세대별 수집으로 효율적 관리
- **Python**: Reference Counting 기본 + Cyclic GC로 순환 참조 탐지
- **TypeScript/JS**: V8 엔진의 Mark-and-Sweep GC
- **Go**: Concurrent GC, Escape Analysis로 스택/힙 자동 결정
- **C++**: `unique_ptr`(단독 소유), `shared_ptr`(공유 소유), `weak_ptr`(약한 참조)
- **Spark**: 각 Executor가 자체 JVM 힙 관리, Shuffle 시 디스크 스필

**Lifetime Scope**:
- **Stack Allocation**: 함수 호출 시 생성, 반환 시 자동 소멸 (빠름)
- **Heap Allocation**: 명시적 할당, GC나 수동 해제 필요 (유연함)
- **Go**: 컴파일러가 Escape Analysis로 스택/힙 자동 결정

**Ownership Model (Rust 비교)**:
Rust의 소유권 모델은 다른 언어에 없는 개념:
- 각 값은 정확히 하나의 소유자를 가짐
- 소유자가 스코프를 벗어나면 값이 드롭됨
- 빌림(borrowing)으로 임시 참조 가능

| 언어 | 소유권 | 빌림 |
|------|--------|------|
| Rust | 명시적, 컴파일 타임 강제 | `&T` (불변), `&mut T` (가변) |
| C++ | `unique_ptr`로 흉내 가능 | 참조로 가능하지만 컴파일러가 강제 안 함 |
| Java/Python/Go | 없음 (공유 참조만) | N/A |

**Reference Counting vs GC**:
- **Reference Counting (Python)**: 참조 수가 0이 되면 즉시 해제. 순환 참조 문제.
- **Tracing GC (Java/Go)**: Root부터 도달 가능한 객체만 유지. 순환 참조 자동 처리.

**Common Pitfalls**:
- **Java**: `static` 컬렉션에 객체 추가 후 제거 안 함 → 영원히 GC 대상 아님
- **Python**: `a.ref = b; b.ref = a` → 순환 참조, Reference Counting으로 해제 불가
- **TypeScript**: 클로저가 큰 객체 캡처 → 클로저 살아있는 동안 메모리 유지
- **C++**: `delete` 후 포인터 사용 → Undefined Behavior
- **Spark**: 큰 DataFrame `.collect()` → Driver OOM

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Memory Model](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html) | Chapter 17. Threads and Locks |
| Java | [GC Tuning](https://docs.oracle.com/en/java/javase/21/gctuning/) | G1, ZGC, Shenandoah |
| Python | [gc module](https://docs.python.org/3/library/gc.html) | Garbage Collector interface |
| Python | [weakref](https://docs.python.org/3/library/weakref.html) | Weak References |
| TypeScript | [Memory Management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Memory_Management) | MDN JavaScript Memory |
| Go | [GC Guide](https://tip.golang.org/doc/gc-guide) | A Guide to the Go Garbage Collector |
| SQL | [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | PostgreSQL MVCC |
| C++ | [Smart Pointers](https://en.cppreference.com/w/cpp/memory) | Memory management library |
| C++ | [RAII](https://en.cppreference.com/w/cpp/language/raii) | Resource Acquisition Is Initialization |
| Spark | [Memory Management](https://spark.apache.org/docs/latest/tuning.html#memory-management-overview) | Tuning Spark |
| Rust | [Ownership](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html) | The Rust Book Ch.4 (참조용) |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- **Python Transforms**: DataFrame 수명 관리, persist/unpersist 이해 필요
- **Java Services**: Spring Bean 라이프사이클, Connection Pool 관리
- **TypeScript OSDK**: Promise 체인에서 메모리 누수 주의
- **Spark Jobs**: Executor 메모리 튜닝, Broadcast 변수 활용

**Interview Relevance**:
- "Java에서 메모리 누수가 발생하는 시나리오를 설명하세요"
- "Python의 Reference Counting과 Java GC의 차이점은?"
- "C++에서 RAII 패턴이 왜 중요한가요?"
- "Spark에서 OOM이 발생할 때 어떻게 디버깅하나요?"
- "Go의 Escape Analysis가 무엇이고 왜 중요한가요?"
- "Weak Reference는 언제 사용하나요? (캐시, 리스너 등)"

**Critical Interview Pattern - Memory Leak 시나리오**:
```
면접관: "이 코드에서 메모리 누수가 있을까요?"

// Java - 누수 있음
public class Cache {
    private static Map<String, Object> cache = new HashMap<>();
    public static void add(String key, Object value) {
        cache.put(key, value);  // remove 없이 계속 추가
    }
}

// Python - 순환 참조
class Node:
    def __init__(self):
        self.parent = None
        self.children = []
    def add_child(self, child):
        self.children.append(child)
        child.parent = self  # 순환!
```

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F01_variable_binding (바인딩과 메모리 할당)
- → F02_mutability_patterns (불변성과 메모리 효율)
- → F10_lexical_scope (스코프와 수명의 관계)
- → F33_thread_safety (동시성에서의 메모리 안전성)
- → F35_gc_mechanisms (GC 알고리즘 상세)

### Existing KB Links
- → 00a_programming_fundamentals (메모리 기초)
- → 22_java_kotlin_backend_foundations (Java 메모리 모델)
- → 30_spark_distributed_computing (Spark 메모리 관리)

### Language-Specific Deep Dives
- **Rust**: 소유권 시스템의 완벽한 구현 (참조 학습용)
- **Swift**: ARC (Automatic Reference Counting) 기반 관리
- **Objective-C**: Manual Retain/Release → ARC 전환 역사

---

## Appendix: Memory Lifecycle Diagram

```
┌────────────────────────────────────────────────────────────┐
│                     Memory Lifecycle                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. Allocation (할당)                                       │
│     Stack: 함수 진입 시 자동                                 │
│     Heap: malloc/new/객체 생성                              │
│                                                            │
│  2. Usage (사용)                                            │
│     변수를 통해 메모리 접근                                   │
│     참조/포인터로 공유 가능                                   │
│                                                            │
│  3. Deallocation (해제)                                     │
│     Manual: free/delete                                    │
│     GC: 도달 불가능할 때 자동                                │
│     RAII: 스코프 종료 시 자동                                │
│     Ownership: 소유자 드롭 시 자동                          │
│                                                            │
│  ⚠️ 위험 구간                                               │
│     - Use-after-free: 해제 후 사용                          │
│     - Double-free: 두 번 해제                               │
│     - Memory leak: 해제 안 함                               │
│     - Dangling pointer: 유효하지 않은 참조                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
