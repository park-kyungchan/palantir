# Knowledge Base Structure Index

> **Purpose**: KB 파일 색인 및 개념 맵 (커리큘럼 아님)
> **Usage**: LLM이 사용자 질문에 맞는 KB를 찾을 때 참조
> **Design**: 정적 색인 - LLM이 동적으로 학습 경로 결정

---

## KB Types Overview

이 Knowledge Base는 두 가지 유형의 KB로 구성됩니다:

### 1. Existing KBs (기존 KB: 00-22)
- Palantir 스택 특화 내용 (Foundry, OSDK, Workshop 등)
- 기존 7-Component 구조 유지
- 수정하지 않고 그대로 활용

### 2. F-Series KBs (신규: F01-F99)
- 프로그래밍 언어 개념 중심 (7개 언어 비교)
- 5-Component 개념 사전 구조
- KB_TEMPLATE.md 기반 생성

---

## F-Series Concept Index

### F01-F09: Binding & Variables (바인딩과 변수)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F01 | variable_binding | 이름과 값을 연결하는 메커니즘 |
| F02 | mutability_patterns | 값 변경 가능성과 제어 방법 |
| F03 | constant_semantics | 상수의 의미와 언어별 구현 차이 |
| F04 | declaration_vs_definition | 선언과 정의의 구분 |
| F05 | shadowing | 동일 이름 변수의 가림 현상 |

### F10-F19: Scope & Lifetime (스코프와 생명주기)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F10 | lexical_scope | 코드 구조에 따른 변수 접근 범위 |
| F11 | closure_capture | 함수가 외부 변수를 캡처하는 방법 |
| F12 | resource_lifetime | 자원의 생성부터 해제까지 관리 |
| F13 | hoisting | 선언이 스코프 상단으로 이동하는 현상 |
| F14 | block_vs_function_scope | 블록 스코프와 함수 스코프 차이 |

### F20-F29: Type Systems (타입 시스템)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F20 | static_vs_dynamic_typing | 타입 검사 시점의 차이 |
| F21 | type_inference | 컴파일러가 타입을 추론하는 방법 |
| F22 | generics_parametric | 타입 매개변수를 통한 다형성 |
| F23 | null_safety | null/nil 값 처리의 안전성 |
| F24 | nominal_vs_structural | 이름 기반 vs 구조 기반 타입 호환성 |
| F25 | type_coercion | 암묵적 타입 변환 |

### F30-F39: Memory & Concurrency (메모리와 동시성)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F30 | memory_models | 메모리 할당과 해제 전략 |
| F31 | concurrency_primitives | 동시성의 기본 구성 요소 |
| F32 | async_patterns | 비동기 프로그래밍 패턴 |
| F33 | thread_safety | 멀티스레드 환경에서의 안전성 |
| F34 | garbage_collection | 자동 메모리 관리 메커니즘 |
| F35 | ownership_borrowing | 소유권과 대여 (Rust 영향) |

### F40-F49: Functions & Control Flow (함수와 제어 흐름)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F40 | function_first_class | 함수를 값으로 다루는 능력 |
| F41 | error_handling_patterns | 에러 처리 전략들 |
| F42 | iteration_patterns | 반복 처리의 다양한 방법 |
| F43 | recursion | 자기 자신을 호출하는 함수 |
| F44 | higher_order_functions | 함수를 인자로 받거나 반환하는 함수 |
| F45 | pure_functions | 부수 효과 없는 함수 |

### F50-F59: Data Structures (자료구조)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F50 | collections_overview | 컬렉션 타입들의 개요 |
| F51 | hash_maps | 키-값 매핑 자료구조 |
| F52 | arrays_vs_lists | 배열과 리스트의 차이 |
| F53 | sets | 중복 없는 값의 집합 |
| F54 | queues_stacks | FIFO와 LIFO 자료구조 |
| F55 | trees_graphs | 계층적/연결 자료구조 |

### F60-F69: Error Handling (에러 처리)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F60 | exceptions_vs_errors | 예외와 에러의 구분 |
| F61 | try_catch_patterns | 예외 처리 구문의 패턴 |
| F62 | result_types | 성공/실패를 타입으로 표현 |
| F63 | error_propagation | 에러를 상위로 전파하는 방법 |

### F70-F79: OOP & Patterns (객체지향과 패턴)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F70 | classes_vs_prototypes | 클래스 기반 vs 프로토타입 기반 |
| F71 | inheritance_composition | 상속과 합성의 선택 |
| F72 | interfaces_protocols | 계약을 정의하는 방법 |
| F73 | encapsulation | 정보 은닉 |
| F74 | polymorphism | 다형성의 다양한 형태 |

### F80-F89: Advanced Topics (고급 주제)

| ID | Concept | Universal Principle |
|----|---------|---------------------|
| F80 | metaprogramming | 코드가 코드를 생성/조작 |
| F81 | reflection | 런타임에 타입 정보 접근 |
| F82 | macros | 컴파일 타임 코드 생성 |
| F83 | lazy_evaluation | 지연 평가 전략 |
| F84 | pattern_matching | 구조에 따른 분기 |

---

## Existing KB Index (00-22)

### Foundation (00x)

| ID | File | Topic | Link to F-Series |
|----|------|-------|------------------|
| 00 | 00_palantir_core_architecture | Palantir 아키텍처 | - |
| 00a | 00a_programming_fundamentals | 프로그래밍 기초 | F01-F05 |
| 00b | 00b_functions_and_scope | 함수와 스코프 | F10-F14, F40-F45 |
| 00c | 00c_data_structures_intro | 자료구조 입문 | F50-F55 |
| 00d | 00d_async_basics | 비동기 기초 | F32 |
| 00e | 00e_typescript_intro | TypeScript 입문 | F20-F25 |

### Frontend (01-03)

| ID | File | Topic |
|----|------|-------|
| 01 | 01_language_foundation | 언어 기초 |
| 02 | 02_react_ecosystem | React 생태계 |
| 03 | 03_styling_systems | 스타일링 시스템 |

### Data & Backend (04-07)

| ID | File | Topic |
|----|------|-------|
| 04 | 04_data_layer | 데이터 레이어 |
| 05 | 05_testing_pyramid | 테스트 피라미드 |
| 06 | 06_build_tooling | 빌드 도구 |
| 07 | 07_version_control | 버전 관리 |

### Advanced (08-10)

| ID | File | Topic |
|----|------|-------|
| 08 | 08_advanced_capabilities | 고급 기능 |
| 09 | 09_orion_system_architecture | Orion 아키텍처 |
| 10 | 10_visual_glossary | 시각적 용어집 |

### Palantir Stack (11-18)

| ID | File | Topic |
|----|------|-------|
| 11 | 11_osdk_typescript | OSDK TypeScript |
| 12 | 12_workshop_development | Workshop 개발 |
| 13 | 13_pipeline_builder | Pipeline Builder |
| 14 | 14_actions_functions | Actions & Functions |
| 15 | 15_slate_dashboards | Slate Dashboards |
| 16 | 16_quiver_analytics | Quiver Analytics |
| 17 | 17_contour_visualization | Contour 시각화 |
| 18 | 18_vertex_ai_models | Vertex AI 모델 |

### Backend Languages (19-22)

| ID | File | Topic | Link to F-Series |
|----|------|-------|------------------|
| 19 | 19_deployment_and_ci_cd | 배포 및 CI/CD | - |
| 20 | 20_go_services_and_concurrency | Go 서비스 | F31, F32 |
| 21 | 21_python_backend_async | Python 백엔드 | F32, F41 |
| 22 | 22_java_kotlin_backend_foundations | JVM 백엔드 | F22, F31 |

---

## How LLM Uses This Index

### 1. 질문 분석
사용자 질문을 받으면 LLM이 자연어 이해로 관련 개념 식별

### 2. KB 검색
이 STRUCTURE.md를 참조하여 관련 KB 파일 식별
- F-Series: 개념 비교가 필요할 때
- Existing KB: Palantir 특화 내용이 필요할 때

### 3. 동적 범위 결정
LLM이 판단하여 "이번 응답에서 어디부터 어디까지" 결정
- 요약 → 상세 → 전체 (Progressive Disclosure)
- Socratic Questioning으로 다음 단계 유도

### 4. 외부 자료 보강
KB 내용이 부족하면:
- WebSearch로 공식 문서 검색
- WebFetch로 고품질 자료 가져오기
- KB 개선점 발견 시 업데이트 제안 (RSIL)

---

## Quality Levels

### Coverage Priority

| Priority | Languages | Requirement |
|----------|-----------|-------------|
| **P0** | Java, Python, TypeScript | 모든 F-Series에 필수 포함 |
| **P1** | Go, SQL | 대부분의 F-Series에 포함 |
| **P2** | C++, Spark | 관련성 높은 F-Series에만 포함 |

### Completeness Levels

| Level | Definition |
|-------|------------|
| **Draft** | Universal Concept만 작성됨 |
| **Basic** | 5-Component 중 3개 이상 완성 |
| **Complete** | 모든 Component 완성 |
| **Verified** | 외부 공식 문서와 교차 검증됨 |

---

## Maintenance Notes

### KB 생성 시
1. KB_TEMPLATE.md 복사
2. F-Series 명명 규칙 준수 (F{NN}_{concept}.md)
3. 이 STRUCTURE.md에 항목 추가
4. Cross-References 연결

### KB 개선 시 (RSIL)
1. 외부 공식 문서 검색
2. 차이점 발견 시 KB 업데이트
3. STRUCTURE.md의 Completeness Level 갱신
4. 변경 이력 기록

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial structure creation |
