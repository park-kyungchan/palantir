# Universal Code Learning Protocol (UCLP) v3.0.0

## Overview

UCLP는 LLM을 활용한 비교 학습 프로토콜로, 4개 언어(Go, Python, Swift, TypeScript)의 철학과 패턴을 동적으로 학습할 수 있도록 설계되었습니다.

**Last Updated**: 2025-12-04
**Version**: 3.0.0
**Status**: Production Ready

---

## Directory Structure

```
/home/palantir/uclp/
├── README.md                          # 이 파일
├── uclp-core.md                       # Tier-0: 핵심 프로토콜 (4.7K)
├── uclp-languages.json                # Tier-1: 언어 메타데이터 (1.4K)
├── uclp-reference.json                # Tier-2: 비교 축 & 예제 (25K, 메인)
├── uclp-languages.schema.json         # JSON 스키마 검증 (1.4K)
├── docs/
│   └── REFERENCE-DESIGN.md            # 설계 문서 (7.5K)
├── examples/
│   └── python_reference_api.py        # Python 조회 API 예제 (5.9K)
├── legacy/
│   ├── uclp-reference-14k.json        # 구 버전 (14K, 축약형)
│   ├── comparison_framework.json      # v2.x 비교 프레임워크 (31K)
│   └── programming_languages_core_philosophy.json  # v2.x 언어 철학 (29K)
└── config/
    └── session.json                   # 세션 설정 예제 (349 bytes)
```

---

## File Description

### Core Files (항상 사용)

| 파일 | 크기 | Tier | 역할 | 상태 |
|------|------|------|------|------|
| `uclp-core.md` | 4.7K | 0 | 프로토콜 정의, 7-section 응답 구조 | ✅ Validated |
| `uclp-languages.json` | 1.4K | 1 | 언어 철학, 패러다임, 주요 특성 | ✅ Validated |
| `uclp-reference.json` | 25K | 2 | 44개 비교 축, 예제 코드, 조회 API | ✅ Validated |
| `uclp-languages.schema.json` | 1.4K | - | JSON Schema 검증용 | ✅ Validated |

### Documentation

| 파일 | 역할 |
|------|------|
| `docs/REFERENCE-DESIGN.md` | uclp-reference.json v3.0.0 설계 문서 |

### Examples

| 파일 | 언어 | 역할 |
|------|------|------|
| `examples/python_reference_api.py` | Python | 참조 데이터 조회 API 예제 |

### Legacy (참고용)

| 파일 | 버전 | 상태 |
|------|------|------|
| `legacy/uclp-reference-14k.json` | v3.0.0-compact | 축약 버전 (사용 비추천) |
| `legacy/comparison_framework.json` | v2.x | 통합됨 → uclp-reference.json |
| `legacy/programming_languages_core_philosophy.json` | v2.x | 통합됨 → uclp-languages.json |

### Configuration

| 파일 | 역할 |
|------|------|
| `config/session.json` | 세션 설정 예제 (레거시) |

---

## Supported Languages

UCLP는 다음 4개 언어를 지원합니다 (Context7 검증 완료, 2025-12-04):

| 언어 | 최신 버전 | Context7 Reputation | Benchmark Score | 상태 |
|------|----------|---------------------|-----------------|------|
| **Go** | v1.25.4 | High | 69.7 | ✅ |
| **Python** | 3.10+ | High | 92.1 | ✅ |
| **Swift** | 6.1.2 | High | 52.5 | ✅ |
| **TypeScript** | 5.9.2 | High | 91.3 | ✅ |

---

## Usage

### 1. LLM 세션에서 UCLP 활성화

```bash
# Tier-0 + Tier-1 로드 (기본 학습)
cat uclp-core.md uclp-languages.json

# Tier-2 참조 (필요시)
cat uclp-reference.json
```

### 2. JSON 스키마 검증

```bash
# Python jsonschema 사용
python3 -c "
import json
import jsonschema

with open('uclp-languages.schema.json') as f:
    schema = json.load(f)
with open('uclp-languages.json') as f:
    data = json.load(f)

jsonschema.validate(data, schema)
print('✅ Validation passed')
"
```

### 3. Python API 예제

```bash
python3 examples/python_reference_api.py
```

---

## Quality Assurance

### 검증 체크리스트

- [x] **JSON 유효성**: 모든 JSON 파일 python3 json.tool 검증 통과
- [x] **Python 구문**: 예제 코드 py_compile 검증 통과
- [x] **마크다운 포맷**: uclp-core.md, REFERENCE-DESIGN.md 구조 확인
- [x] **디렉토리 권한**: 755 (읽기/실행 모든 사용자 가능)
- [x] **파일 크기**: 25K 버전이 메인으로 사용됨
- [x] **버전 일관성**: v3.0.0 전체 파일 일치

### 검증 결과 (2025-12-04)

| 파일 | 검증 유형 | 결과 | 비고 |
|------|----------|------|------|
| uclp-core.md | Markdown | ✅ OK | Tier-0 프로토콜 정의 |
| uclp-languages.json | JSON | ✅ VALID | 언어 메타데이터 |
| uclp-languages.schema.json | JSON | ✅ VALID | 스키마 검증 |
| uclp-reference.json | JSON | ✅ VALID | 25K 메인 참조 |
| REFERENCE-DESIGN.md | Markdown | ✅ OK | 설계 문서 |
| python_reference_api.py | Python | ✅ VALID | 예제 코드 |
| uclp-reference-14k.json | JSON | ✅ VALID | 레거시 (축약형) |
| comparison_framework.json | JSON | ✅ VALID | 레거시 (v2.x) |
| programming_languages_core_philosophy.json | JSON | ✅ VALID | 레거시 (v2.x) |
| session.json | JSON | ✅ VALID | 세션 설정 예제 |

---

## Migration Summary

### 원본 → 신규 위치 매핑

| 원본 | 신규 | 역할 |
|------|------|------|
| `/home/palantir/coding/uclp-core.md` | `uclp-core.md` | 메인 |
| `/home/palantir/coding/uclp-languages.json` | `uclp-languages.json` | 메인 |
| `/home/palantir/coding/uclp-languages.schema.json` | `uclp-languages.schema.json` | 메인 |
| `/home/palantir/coding/references/uclp_reference.json` (25K) | `uclp-reference.json` | 메인 |
| `/home/palantir/coding/uclp-reference.json` (14K) | `legacy/uclp-reference-14k.json` | 레거시 |
| `/home/palantir/coding/references/uclp_reference_summary.md` | `docs/REFERENCE-DESIGN.md` | 문서 |
| `/home/palantir/coding/references/uclp_reference_api_example.py` | `examples/python_reference_api.py` | 예제 |
| `/home/palantir/coding/references/comparison_framework.json` | `legacy/comparison_framework.json` | 레거시 |
| `/home/palantir/coding/references/programming_languages_core_philosophy.json` | `legacy/programming_languages_core_philosophy.json` | 레거시 |
| `/home/palantir/uclp_session_config.json` | `config/session.json` | 설정 |

**참고**: 원본 파일은 `/home/palantir/coding/`에 그대로 유지되며, `/home/palantir/uclp/`는 정리된 복사본입니다.

---

## Next Steps

### Sub-C (문서화) 전달 준비 상태

1. **구조 확정**: ✅ 4-tier 디렉토리 구조 완성
2. **검증 완료**: ✅ JSON/Python/Markdown 모두 통과
3. **메타데이터**: ✅ README.md 작성 완료
4. **버전 정보**: ✅ v3.0.0 일관성 확인

### 추천 작업

- [ ] CHANGELOG.md 작성 (v2.x → v3.0.0 변경 사항)
- [ ] CONTRIBUTING.md 작성 (협업 가이드)
- [ ] 예제 확장 (Go, Swift, TypeScript API 예제)
- [ ] CI/CD 파이프라인 구성 (자동 검증)

---

## References

- **CLAUDE.md**: `/home/palantir/.claude/CLAUDE.md` (Multi-Agent Orchestration Protocol 참고)
- **Context7 검증**: 2025-12-04 수행 (4개 언어 최신성 확인)
- **설계 문서**: `docs/REFERENCE-DESIGN.md`

---

## License

Internal use only (Palantir project)

---

**Generated**: 2025-12-04
**Tool**: Claude Code (Sonnet 4.5)
**Protocol**: UCLP v3.0.0
