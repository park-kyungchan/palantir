# UCLP Reference v3.0.0 설계안

## 1. 개요

**파일명**: `uclp-reference.json`
**크기**: 24,937 bytes (~25KB, 목표 40KB 미만 달성)
**버전**: 3.0.0
**역할**: UCLP Tier-2 참조 문서 - 필요시 조회하는 비교 축, 예제, 공식 문서 저장소

## 2. 설계 원칙

### 2.1 조회 최적화
- **인덱싱 구조**: concept_id와 language로 O(1) 조회
- **필요시 로드**: 전체가 아닌 필요한 부분만 조회
- **메타데이터 제외**: changelog, compatibility, usage_instructions 등 개발 메타데이터 미포함

### 2.2 압축 전략
| 섹션 | 원본 크기 | 압축 후 | 압축률 | 전략 |
|------|----------|---------|--------|------|
| comparison_axes | ~7KB | ~4.4KB | 37% | how_to_compare 제거 |
| example_explanations | ~8.5KB | ~5KB | 41% | historical_context, tradeoff 제거 (동적 생성) |
| concept_categories | ~3KB | ~1.5KB | 50% | prerequisites/related 간소화 |
| depth_selection | ~2.5KB | ~1.5KB | 40% | 알고리즘 핵심만 유지 |
| **총합** | ~78KB | ~25KB | 68% | |

## 3. 구조

```json
{
  "version": "3.0.0",
  "comparison_framework": {
    "categories": {
      "basics": { "required_axes": [...], "concepts": [...] },
      ...
    },
    "axes": {
      "syntax": { "name": "...", "description": "..." },
      ...
    },
    "idiomatic_patterns": {
      "go": [...],
      "python": [...],
      "swift": [...],
      "typescript": [...]
    }
  },
  "examples": {
    "variable_declaration": {
      "go": { "syntax": "...", "design_decision": "...", "sources": [...] }
    },
    "error_handling": {...},
    "concurrency": {...}
  },
  "sources": {
    "go": [...],
    "python": [...],
    "swift": [...],
    "typescript": [...]
  },
  "depth_selection": {
    "levels": [...],
    "indicators": {...}
  },
  "code_validation": {
    "go": { "light": {...}, "strict": {...} },
    ...
  }
}
```

## 4. 포함 내용

### 4.1 comparison_framework
- **categories (8개)**: basics, functions, data_structures, error_handling, concurrency, abstraction, modules, memory
- **axes (44개)**: syntax, philosophy, tradeoff, type_system, error_model, concurrency_model 등
- **required_axes_per_category**: 카테고리별 필수 비교 축 목록
- **idiomatic_patterns**: 언어별 관용구 패턴 5개씩
- **concepts**: 각 카테고리별 개념 목록 (id, name, prerequisites, related)

### 4.2 examples
- **variable_declaration**: 4개 언어 예제
- **error_handling**: 4개 언어 예제
- **concurrency**: 4개 언어 예제

각 예제 포함 정보:
- `syntax`: 구문 요약
- `design_decision`: 설계 결정 설명
- `sources`: 공식 문서 링크 배열

### 4.3 sources
- Go: 4개 (Documentation, Blog, Talks, Proposals)
- Python: 3개 (Documentation, PEPs, Real Python)
- Swift: 4개 (Documentation, Evolution, Apple Docs, Swift by Sundell)
- TypeScript: 4개 (Documentation, Design Goals, Wiki, Deep Dive)

### 4.4 depth_selection
- `levels`: ["beginner", "intermediate", "advanced"]
- `indicators`: 각 레벨별 키워드 목록
- `level_response_differences`: 레벨별 포함/제외 내용

### 4.5 code_validation
- 4개 언어 × 2개 모드 (light, strict)
- 각 모드별: command, fallback, description

## 5. 조회 API

### 5.1 예제 조회
```python
get_example(concept_id: str, language: str) -> dict
# 예: get_example("error_handling", "go")
# 반환: {"syntax": "...", "design_decision": "...", "sources": [...]}
```

### 5.2 비교 축 조회
```python
get_required_axes(category: str) -> list[str]
# 예: get_required_axes("basics")
# 반환: ["syntax", "type_system", "default_value", ...]
```

### 5.3 축 정의 조회
```python
get_axis_definition(axis_id: str) -> dict
# 예: get_axis_definition("syntax")
# 반환: {"name": "Syntax", "description": "..."}
```

### 5.4 검증 명령어 조회
```python
get_validation_command(language: str, mode: str = "light") -> str
# 예: get_validation_command("python", "light")
# 반환: "python3 -m py_compile {file}"
```

### 5.5 공식 문서 조회
```python
get_sources(language: str) -> list[dict]
# 예: get_sources("swift")
# 반환: [{"title": "...", "url": "...", "type": "official_doc"}, ...]
```

### 5.6 관용구 패턴 조회
```python
get_idiomatic_patterns(language: str) -> list[dict]
# 예: get_idiomatic_patterns("go")
# 반환: [{"pattern": "if err != nil", "usage": "...", "philosophy": "..."}, ...]
```

## 6. 제외된 내용 및 이유

| 제외 항목 | 이유 | 대안 |
|----------|------|------|
| metadata, versioning, changelog | 개발 메타데이터 | 별도 관리 |
| compatibility, definitions | 스키마 정의 | $schema로 참조 |
| response_structure | Tier-1 프로토콜 포함 | 메인 프로토콜 사용 |
| dynamic_context | 생성 프로토콜 | 메인 프로토콜 사용 |
| historical_context (in examples) | 동적 생성 가능 | LLM이 응답 시 생성 |
| tradeoff (in examples) | 동적 생성 가능 | LLM이 응답 시 생성 |
| how_to_compare (in axes) | 상세 지침 | description만으로 충분 |

## 7. 사용 시나리오

### 시나리오 1: 비교 테이블 생성
```
1. get_required_axes("error_handling") → 필수 축 목록
2. for each axis: get_axis_definition(axis_id) → 축 정의
3. 각 언어별 값 채움 (LLM 지식 + examples 참조)
```

### 시나리오 2: 예제 확장
```
1. get_example("error_handling", "go") → 기본 예제
2. get_sources("go") → 공식 문서
3. LLM이 historical_context, tradeoff 동적 생성
```

### 시나리오 3: 코드 검증
```
1. get_validation_command("python", "light") → 명령어
2. 파일 경로 대체: {file} → actual_file.py
3. 실행 및 결과 반환
```

### 시나리오 4: 학습 경로 추천
```
1. get_concepts_by_category("basics") → 개념 목록
2. 각 concept의 prerequisites 확인
3. 위상 정렬로 학습 순서 생성
```

## 8. 버전 관리

- **Major (3.x.x)**: 구조 변경 (소스 v2.2.0 → v3.0.0, Tier-2 분리)
- **Minor (x.1.x)**: 언어 추가 또는 카테고리 추가
- **Patch (x.x.1)**: 예제 추가, 소스 추가, 오타 수정

## 9. 검증 결과

```bash
$ ls -lh uclp-reference.json
-rw------- 1 palantir palantir 25K Dec  1 10:08 uclp-reference.json

$ python3 -c "import json; ..."
✓ JSON 유효함
버전: 3.0.0
카테고리 수: 8
축 수: 44
예제 개념 수: 3
```

## 10. 파일 목록

1. **uclp-reference.json** (25KB)
   - Tier-2 참조 문서 본체

2. **uclp_reference_api_example.py**
   - Python 조회 API 구현 예제
   - UCLPReference 클래스
   - 6가지 조회 함수 포함

3. **uclp-reference-summary.md** (본 문서)
   - 설계안 요약

## 11. 향후 확장

### 11.1 언어 추가 (예: Rust)
```json
{
  "examples": {
    "error_handling": {
      "rust": {
        "syntax": "let data = func()?;",
        "design_decision": "Result<T, E> with ? operator...",
        "sources": [...]
      }
    }
  },
  "sources": {
    "rust": [...]
  }
}
```
→ 예상 추가 크기: ~3KB (35KB 미만 유지)

### 11.2 예제 개념 추가
현재 3개 (variable_declaration, error_handling, concurrency)
추가 가능: async_await, generics, interfaces_protocols
→ 각 ~1.5KB, 최대 3개 추가 시 ~30KB

## 12. 결론

✅ **목표 달성**:
- 크기: 25KB < 40KB 제약
- 인덱싱: O(1) 조회 구조
- 완결성: 8개 카테고리, 44개 축, 3개 예제, 4개 언어

✅ **설계 품질**:
- 조회 API 6종 제공
- Python 예제 코드 동작 검증
- JSON Schema 호환

✅ **확장성**:
- 언어 추가: ~3KB/언어
- 예제 추가: ~1.5KB/개념
- 15KB 여유 (40KB - 25KB)
