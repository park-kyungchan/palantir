# Contributing to UCLP

Universal Code Learning Protocol에 기여해 주셔서 감사합니다! 이 문서는 UCLP 프로젝트에 기여하는 방법을 안내합니다.

---

## 📋 목차 (Table of Contents)

1. [새로운 언어 추가](#새로운-언어-추가)
2. [예제 코드 추가/수정](#예제-코드-추가수정)
3. [비교 축 추가/수정](#비교-축-추가수정)
4. [검증 기준](#검증-기준)
5. [PR 가이드라인](#pr-가이드라인)
6. [코드 스타일](#코드-스타일)

---

## 🌐 새로운 언어 추가

UCLP에 새로운 프로그래밍 언어를 추가하려면 다음 단계를 따르세요.

### 1단계: uclp-languages.json 수정

`uclp-languages.json` 파일에 새 언어 엔트리를 추가합니다.

**필수 필드**:
```json
{
  "languages": {
    "rust": {
      "name": "Rust",
      "version": "1.85.0",
      "paradigms": ["imperative", "functional", "concurrent"],
      "typing": "static_strong_inferred",
      "memory_model": "ownership",
      "primary_use_cases": [
        "systems_programming",
        "embedded",
        "web_assembly",
        "cli_tools"
      ],
      "philosophy": {
        "core_principles": [
          "memory safety without garbage collection",
          "zero-cost abstractions",
          "fearless concurrency"
        ],
        "design_priorities": [
          "safety",
          "performance",
          "concurrency"
        ]
      },
      "key_features": {
        "ownership_system": "Compile-time memory safety guarantees",
        "borrowing": "References with lifetime tracking",
        "trait_system": "Polymorphism without inheritance",
        "async_await": "Zero-cost asynchronous programming"
      }
    }
  }
}
```

**검증**:
```bash
# JSON 유효성 검증
python3 -m json.tool uclp-languages.json > /dev/null && echo "✅ Valid JSON"

# JSON Schema 검증
python3 -c "
import json
import jsonschema

with open('uclp-languages.schema.json') as f:
    schema = json.load(f)
with open('uclp-languages.json') as f:
    data = json.load(f)

jsonschema.validate(data, schema)
print('✅ Schema validation passed')
"
```

---

### 2단계: uclp-reference.json 확장

`uclp-reference.json`에 새 언어의 비교 축 데이터를 추가합니다.

#### 2-1. 범용 축 (Common Axes) 업데이트

6개 범용 축에 대한 언어별 값 추가:

```json
{
  "common_axes": {
    "typing_discipline": {
      "values": {
        "rust": "static_strong_inferred"
      }
    },
    "type_inference": {
      "values": {
        "rust": "extensive"
      }
    },
    "memory_management": {
      "values": {
        "rust": "manual_ownership"
      }
    },
    "concurrency_model": {
      "values": {
        "rust": "fearless_concurrency"
      }
    },
    "error_handling_primary": {
      "values": {
        "rust": "result_type"
      }
    },
    "paradigm_primary": {
      "values": {
        "rust": "multi_paradigm"
      }
    }
  }
}
```

#### 2-2. 카테고리별 축 (Category Axes) 업데이트

각 카테고리(type_system, memory, concurrency, error_handling, paradigm, tooling)의 세부 축에 대한 값 추가.

**예시 - Type System**:
```json
{
  "categories": {
    "type_system": {
      "axes": {
        "type_safety": {
          "values": {
            "rust": "strong_static"
          },
          "description": "Compile-time type checking prevents most type errors"
        },
        "generics_support": {
          "values": {
            "rust": "full_parametric"
          },
          "description": "Full parametric polymorphism with trait bounds"
        }
      }
    }
  }
}
```

#### 2-3. 예제 코드 추가

각 카테고리별 대표 예제 코드 추가:

```json
{
  "examples": {
    "type_system": {
      "rust": "struct Point<T> {\n    x: T,\n    y: T,\n}\n\nimpl<T> Point<T> {\n    fn new(x: T, y: T) -> Self {\n        Point { x, y }\n    }\n}"
    },
    "concurrency": {
      "rust": "use tokio::task;\n\n#[tokio::main]\nasync fn main() {\n    let handle = task::spawn(async {\n        // Async work\n        42\n    });\n    \n    let result = handle.await.unwrap();\n    println!(\"Result: {}\", result);\n}"
    },
    "error_handling": {
      "rust": "use std::fs::File;\nuse std::io::Read;\n\nfn read_file(path: &str) -> Result<String, std::io::Error> {\n    let mut file = File::open(path)?;\n    let mut contents = String::new();\n    file.read_to_string(&mut contents)?;\n    Ok(contents)\n}"
    }
  }
}
```

---

### 3단계: Context7 검증 (선택 사항)

Context7 MCP를 사용하여 추가된 언어의 정확성을 검증합니다.

```bash
# Context7 resolve-library-id
mcp__context7__resolve-library-id --libraryName "rust"

# Context7 get-library-docs (공식 문서 확인)
mcp__context7__get-library-docs \
  --context7CompatibleLibraryID "/rust-lang/rust" \
  --mode info \
  --topic "ownership memory safety"
```

**검증 항목**:
- [ ] 철학(core_principles) 공식 문서와 일치
- [ ] 주요 기능(key_features) 최신 버전 반영
- [ ] 예제 코드 실행 가능 및 관용적(idiomatic)
- [ ] 타입 시스템/메모리 모델 정확성

---

## 📝 예제 코드 추가/수정

### 예제 코드 작성 원칙

1. **실행 가능성 (Executable)**: 모든 예제는 해당 언어의 컴파일러/인터프리터에서 실행 가능해야 함
2. **관용성 (Idiomatic)**: 해당 언어의 모범 사례(best practices)를 따름
3. **간결성 (Concise)**: 핵심 개념을 보여주는 최소한의 코드
4. **주석 금지 (No Comments)**: 코드 자체가 자명해야 함 (예외: 복잡한 알고리즘)

### 예제 검증 체크리스트

- [ ] **구문 검증**: 해당 언어의 linter/compiler로 검증
  ```bash
  # Go
  go fmt example.go && go vet example.go

  # Python
  python3 -m py_compile example.py

  # Swift
  swiftc -parse example.swift

  # TypeScript
  tsc --noEmit example.ts

  # Rust (추가 예정)
  rustc --crate-type lib example.rs
  ```

- [ ] **실행 가능**: 실제로 실행하여 오류 없음 확인
- [ ] **최신 문법**: 해당 언어의 최신 안정 버전 문법 사용
- [ ] **크기 제한**: 20줄 이내 (복잡한 경우 30줄까지 허용)

### 나쁜 예제 vs 좋은 예제

**❌ 나쁜 예제 (TypeScript - 현재 이슈 #1)**:
```typescript
// 함수명이 global fetch와 충돌
async function fetch(): Promise<Data> {
    const response = await fetch(url);  // 재귀 우려
    return response.json();
}
```

**✅ 좋은 예제**:
```typescript
async function fetchData(): Promise<Data> {
    const response = await fetch(url);  // global API 명확
    return response.json();
}
```

---

## 🔍 비교 축 추가/수정

### 새로운 비교 축 제안

새로운 비교 축을 추가하려면:

1. **필요성 검증**: 4개 언어 모두에서 의미 있는 차이가 있는가?
2. **카테고리 선택**: type_system, memory, concurrency, error_handling, paradigm, tooling 중 하나
3. **값 정의**: 각 언어별로 명확한 값 정의

**제안 템플릿**:
```json
{
  "axis_name": "new_axis",
  "category": "type_system",
  "description": "명확한 설명",
  "values": {
    "go": "value_for_go",
    "python": "value_for_python",
    "swift": "value_for_swift",
    "typescript": "value_for_typescript"
  },
  "rationale": "왜 이 축이 필요한가?"
}
```

### 기존 축 수정

기존 축의 값을 수정하려면:
1. **공식 문서 확인**: 수정 근거가 공식 문서에 있는가?
2. **Context7 검증**: 최신 정보와 일치하는가?
3. **이유 명시**: PR에 수정 이유와 근거 포함

---

## ✅ 검증 기준

모든 기여는 다음 기준을 만족해야 합니다.

### 자동 검증 (Automated Validation)

```bash
# 1. JSON 유효성 검증
find . -name "*.json" -exec python3 -m json.tool {} \; > /dev/null

# 2. Python 구문 검증
find examples/ -name "*.py" -exec python3 -m py_compile {} \;

# 3. Markdown 검증 (선택 사항)
# markdownlint 사용 시
markdownlint *.md docs/*.md
```

### 수동 검증 (Manual Validation)

- [ ] **철학 일치도**: 공식 문서와 비교하여 95% 이상 일치
- [ ] **예제 품질**: 실행 가능하고 관용적인 코드
- [ ] **일관성**: 기존 스타일 및 구조와 일관성 유지
- [ ] **버전 정보**: 최신 안정 버전 명시

---

## 🔀 PR 가이드라인

### PR 제출 전 체크리스트

- [ ] JSON 유효성 검증 통과
- [ ] 예제 코드 실행 가능
- [ ] CHANGELOG.md 업데이트 (버전 정보)
- [ ] 변경 사항 테스트 완료
- [ ] 커밋 메시지 명확 (conventional commits 권장)

### PR 템플릿

```markdown
## 변경 내용 (Changes)

- [간결한 설명]

## 변경 유형 (Type of Change)

- [ ] 새로운 언어 추가
- [ ] 예제 코드 수정
- [ ] 비교 축 추가/수정
- [ ] 문서 업데이트
- [ ] 버그 수정

## 검증 (Validation)

- [ ] JSON 유효성 검증 통과
- [ ] 예제 코드 실행 테스트 완료
- [ ] Context7 검증 (선택 사항)

## 관련 이슈 (Related Issues)

Fixes #123

## 추가 정보 (Additional Information)

[필요시 추가 설명]
```

### 커밋 메시지 규칙

Conventional Commits 형식 권장:

```bash
# 새로운 언어 추가
feat(languages): add Rust language support

# 예제 수정
fix(examples): correct TypeScript fetch function name collision

# 문서 업데이트
docs(readme): update migration guide for v3.0.0

# 비교 축 추가
feat(axes): add generics_support axis to type_system category
```

---

## 🎨 코드 스타일

### JSON 포맷팅

- **들여쓰기**: 2 spaces
- **키 순서**: 알파벳 순서 유지 (선택 사항)
- **줄바꿈**: 80자 제한 없음 (가독성 우선)

**포맷팅 도구**:
```bash
# Python json.tool
python3 -m json.tool input.json > output.json

# jq (권장)
jq '.' input.json > output.json
```

### Markdown 스타일

- **제목**: ATX 스타일 (`#`, `##`) 사용
- **목록**: `-` 사용 (일관성)
- **코드 블록**: 언어 명시 필수
- **줄바꿈**: 섹션 사이 `---` 구분선 사용

---

## 📚 참고 자료

- **UCLP 설계 문서**: `docs/REFERENCE-DESIGN.md`
- **개선 권고사항**: `recommendations.md`
- **Context7 MCP**: Claude Code MCP Tools
- **Conventional Commits**: https://www.conventionalcommits.org/

---

## 🙋 질문 및 지원

- **이슈 제기**: GitHub Issues (프로젝트 저장소)
- **토론**: GitHub Discussions (아이디어, 제안)
- **긴급 수정**: PR 직접 제출

---

**마지막 업데이트**: 2025-12-04
**버전**: v3.0.0
**작성자**: UCLP Contributors
