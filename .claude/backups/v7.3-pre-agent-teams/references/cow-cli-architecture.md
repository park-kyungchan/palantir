# COW CLI - Mathpix API Architecture

> **Version:** 2.0 | **Created:** 2026-02-04 | **Updated:** 2026-02-04
> **Location:** `/home/palantir/cow/cow-cli`

---

## 1. Overview

COW CLI는 Mathpix API를 활용하여 수학 문서(PDF/이미지)를 처리하고 Layout/Content를 분리하며, PDF를 재구성하는 파이프라인입니다.

### Core Principles

```
API-FIRST      → Mathpix API 문서 기준 스키마 설계
NORMALIZE      → PDF/Image API 응답을 UnifiedResponse로 통합
HIERARCHY      → parent_id/children_ids로 문서 구조 보존
SEPARATION     → Layout(위치/구조) vs Content(텍스트/수식) 분리
```

---

## 2. Architecture

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COW CLI Pipeline (v2.0)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [입력]                                                        │
│     │                                                           │
│     ├── PDF ─────┐                                              │
│     │            │                                              │
│     └── Image ───┼──▶ MathpixClient                             │
│                  │    ├── process_pdf() → /v3/pdf               │
│                  │    └── process_image_unified() → /v3/text    │
│                  │         │                                    │
│                  │         ▼                                    │
│                  │    UnifiedResponse                           │
│                  │    (PDF/Image 통합 정규화)                   │
│                  │         │                                    │
│                  │         ▼                                    │
│                  │    LayoutContentSeparator                    │
│                  │    ├── separate_unified()                    │
│                  │    ├── get_hierarchy()                       │
│                  │    └── get_subtree()                         │
│                  │         │                                    │
│                  │    ┌────┴────┐                               │
│                  │    │         │                               │
│                  │    ▼         ▼                               │
│                  │  Layout   Content                            │
│                  │  (위치,   (텍스트,                           │
│                  │   구조)    수식)                             │
│                  │    │         │                               │
│                  │    └────┬────┘                               │
│                  │         ▼                                    │
│                  │    Export (JSON/MD/LaTeX)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| MathpixClient | `cow_cli/mathpix/client.py` | API 클라이언트 |
| Schemas | `cow_cli/mathpix/schemas.py` | Pydantic 모델 |
| Separator | `cow_cli/semantic/separator.py` | Layout/Content 분리 |
| CLI | `cow_cli/commands/process.py` | CLI 명령어 |

---

## 3. Schema Design

### UnifiedResponse Pattern

PDF API와 Image API의 응답 차이를 해결하기 위한 통합 응답 모델:

```python
# PDF API: pages[] -> lines[]
# Image API: line_data[]

# UnifiedResponse로 통합:
class UnifiedResponse(BaseModel):
    metadata: ResponseMetadata
    pages: List[PdfPageData]  # Image도 pages[0]으로 정규화
    raw_response: Optional[dict]

    @classmethod
    def from_pdf_response(cls, pdf_id, lines_data, status_data):
        # PDF API 응답 정규화

    @classmethod
    def from_image_response(cls, response_data):
        # Image API 응답 정규화 (line_data -> pages[0].lines)
```

### PdfLineData Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | 고유 식별자 |
| `type` | str | section_header, text, equation, diagram 등 |
| `subtype` | str? | equation_inline, equation_block 등 |
| `text` | str | 검색용 텍스트 |
| `text_display` | str? | 렌더링용 Mathpix Markdown |
| `parent_id` | str? | 부모 요소 ID |
| `children_ids` | List[str]? | 자식 요소 ID 리스트 |
| `cnt` | List[[x,y]] | 폴리곤 좌표 |
| `region` | Region? | Bounding box |
| `confidence` | float? | [0,1] 인식 정확도 |
| `confidence_rate` | float? | [0,1] 품질 점수 |

---

## 4. Hierarchy Handling

### Structure Preservation

```python
# 문서 계층 구조 예시:
# section_header (parent_id=None)
#   └── text (parent_id=section_header.id)
#   └── equation (parent_id=section_header.id)
#       └── equation_inline (parent_id=equation.id)

# Separator 메서드:
separator = LayoutContentSeparator()
document = separator.separate_unified(unified)

# 계층 탐색:
hierarchy = separator.get_hierarchy(document.layout)
# {"section_header_id": ["text_id", "equation_id"]}

roots = separator.get_root_elements(document.layout)
# ["section_header_id"]

subtree = separator.get_subtree(document.layout, "section_header_id")
# [section_header, text, equation, equation_inline]
```

---

## 5. text vs text_display

| Field | Purpose | Example |
|-------|---------|---------|
| `text` | 검색/인덱싱용 | `f(x) = x^2` |
| `text_display` | 렌더링/출력용 | `$f(x) = x^2$` |

### Usage

```python
# 검색 시:
searchable = element.text.lower()

# 렌더링 시 (Markdown/LaTeX):
rendered = element.text_display

# Export 시:
if format == "plain":
    output = element.text
else:
    output = element.text_display
```

---

## 6. CLI Usage

```bash
# PDF 처리 (직접 API)
cow process pdf /path/to/document.pdf -o output/

# 이미지 처리
cow process image /path/to/image.png -o output/

# 배치 처리
cow process batch /path/to/images/ -p "*.png" -j 4
```

---

## 7. Sub-Orchestrator Pattern

이 아키텍처 리팩토링에서 사용된 오케스트레이션 패턴:

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Execute  │────▶│ Validate │────▶│ Decision │────▶│ Unblock  │
│  Task    │     │  Output  │     │   Gate   │     │  Next    │
└──────────┘     └──────────┘     └────┬─────┘     └────┬─────┘
                                       │                 │
         ┌────────────── PASS ─────────┘                 │
         │                                               │
         ▼                                               ▼
    ┌──────────┐                                    ┌──────────┐
    │ Mark     │                                    │ Pick     │
    │ COMPLETE │───────────────────────────────────▶│ Next     │
    └──────────┘                                    └────┬─────┘
                                                        │
         ┌────────────── FAIL ──────────────────────────┘
         │
         ▼
    ┌──────────┐
    │ Fix &    │──────────────────▶ (Loop back to Execute)
    │ Retry    │
    └──────────┘
```

### Task Dependencies

```
Phase 1 (Schema) → Phase 2 (Client) → Phase 3 (Separator) → Phase 4 (Cleanup) → Phase 5 (Test)
```

---

## 8. API Reference

### Mathpix API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v3/pdf` | POST | PDF 업로드 |
| `/v3/pdf/{id}` | GET | 처리 상태 조회 |
| `/v3/pdf/{id}.lines.json` | GET | 라인 데이터 조회 |
| `/v3/text` | POST | 이미지 OCR |

### Context7 Library

```
Library ID: /websites/mathpix
Code Snippets: 107
Source Reputation: High
```

---

## 9. PDF Reconstruction Pipeline (v2.0)

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PDF Reconstruction Pipeline (v2.0)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [B1 Outputs]                                                              │
│     │                                                                       │
│     ├── layout.json ────┐                                                   │
│     │                   │                                                   │
│     └── content.json ───┼──▶ MMDMerger                                      │
│                         │    └── merge_files()                              │
│                         │         │                                         │
│                         │         ▼                                         │
│                         │    Mathpix Markdown (MMD)                         │
│                         │         │                                         │
│                         │         ▼                                         │
│                         │    MathpixPDFConverter                            │
│                         │    ├── convert() → /v3/converter                  │
│                         │    └── get_status() (async polling)               │
│                         │         │                                         │
│                         │         ▼                                         │
│                         │    Reconstructed PDF                              │
│                         │         │                                         │
│                         │         ▼                                         │
│                         │    ReconstructionValidator                        │
│                         │    ├── validate()                                 │
│                         │    ├── text_coverage (≥90%)                       │
│                         │    ├── math_coverage (≥85%)                       │
│                         │    └── layout_order (≥95%)                        │
│                         │         │                                         │
│                         │    ┌────┴────┐                                    │
│                         │    │         │                                    │
│                         │    ▼         ▼                                    │
│                         │  PASS     FAIL                                    │
│                         │    │         │                                    │
│                         │    ▼         ▼                                    │
│                         │  Output   Human Review                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| MMDMerger | `cow_cli/pdf/merger.py` | Layout+Content → MMD 병합 |
| MathpixPDFConverter | `cow_cli/pdf/converter.py` | MMD → PDF 변환 |
| ReconstructionValidator | `cow_cli/pdf/validator.py` | PDF 품질 검증 |

### MCP Tools (cow-pdf server)

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `merge_to_mmd` | B1 outputs → MMD | layout_path, content_path | mmd_content, warnings |
| `convert_to_pdf` | MMD → PDF | mmd_content, output_path | pdf_path, conversion_id |
| `validate_reconstruction` | Quality check | pdf_path, layout_path, content_path | scores, issues |
| `get_reconstruction_status` | Async polling | conversion_id | status, progress, pdf_url |

### Quality Thresholds

| Metric | Acceptable | Good | Human Review Trigger |
|--------|------------|------|---------------------|
| Text Coverage | ≥ 90% | ≥ 95% | < 80% |
| Math Coverage | ≥ 85% | ≥ 90% | < 70% |
| Layout Order | ≥ 95% | ≥ 98% | < 80% |

### Claude Assistor Role

Claude-Opus-4.5는 PDF Reconstruction에서 다음 역할만 수행:

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Claude Assistor Role                              │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ ORCHESTRATOR  │  Tool 호출 조율, 워크플로우 관리                │
│  ✅ VALIDATOR     │  품질 검증, 임계값 판단, 데이터 무결성          │
│  ✅ RECOMMENDER   │  개선 제안, 에러 복구, 휴먼 리뷰 큐잉          │
├─────────────────────────────────────────────────────────────────────┤
│  ❌ NOT A PERFORMER                                                 │
│  Claude는 직접 OCR, PDF 생성, 변환을 수행하지 않음                 │
│  모든 실행은 MCP Tools (cow-pdf, cow-mathpix)에게 위임             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Module Structure

```
cow_cli/
├── mathpix/                    # Mathpix API Integration
│   ├── client.py               # MathpixClient
│   ├── schemas.py              # Pydantic models (UnifiedResponse)
│   └── exceptions.py           # Custom exceptions
│
├── semantic/                   # Layout/Content Separation
│   ├── separator.py            # LayoutContentSeparator
│   └── schemas.py              # LayoutData, ContentData
│
├── pdf/                        # PDF Reconstruction (v2.0)
│   ├── __init__.py             # Package exports
│   ├── merger.py               # MMDMerger
│   ├── converter.py            # MathpixPDFConverter
│   ├── validator.py            # ReconstructionValidator
│   └── tests/                  # 56 test functions
│       ├── test_merger.py
│       ├── test_converter.py
│       ├── test_validator.py
│       └── test_e2e_reconstruction.py
│
├── claude/                     # Claude Agent SDK Integration
│   └── mcp_servers.py          # MCP tool definitions
│       ├── cow-mathpix         # Mathpix API tools
│       ├── cow-separator       # Separation tools
│       ├── cow-validation      # Validation tools
│       ├── cow-hitl            # Human-in-the-loop tools
│       └── cow-pdf             # PDF reconstruction tools (NEW)
│
└── commands/                   # CLI Commands
    └── process.py              # PDF/Image processing
```

---

> **Changelog:**
> - v2.0 (2026-02-04): Added PDF Reconstruction Pipeline (cow-pdf module)
>   - MMDMerger, MathpixPDFConverter, ReconstructionValidator
>   - 4 MCP tools: merge_to_mmd, convert_to_pdf, validate_reconstruction, get_reconstruction_status
>   - Quality thresholds and Claude Assistor role
>   - 56 test functions across 14 test classes
> - v1.0 (2026-02-04): Initial architecture documentation
