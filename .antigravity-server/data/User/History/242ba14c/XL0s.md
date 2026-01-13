# Phase 11: UDM Schema and Reusable Action Templates

## Background (OWPML Architecture Report)
> "HWPX는 문서를 단일 파일이 아닌 논리적으로 연관된 리소스들의 집합체(Package)로 정의하고, 각 리소스를 XML, 이미지, 바이너리 객체 등으로 세분화하여 구조화된 압축 컨테이너(ZIP) 내에 저장하는 방식을 취한다."

Key insight from user's OWPML analysis:
- **Declaration과 Reference 분리**: header.xml에 스타일 선언, section.xml에서 ID로 참조
- **Unified Document Model (UDM)**: 참조를 인라인으로 풀어 JSON 형태로 변환

---

## Goal
1. **Create reusable Action Template Library** for math workbook documents
2. **Implement 2-column layout detection** (sample.pdf: 좌=4,5,6 / 우=7,8,9)
3. **Create UDM JSON Schema** based on OWPML report
4. **Fix output_actions.json** to include missing layout elements

---

## Proposed Changes

### Component 1: UDM JSON Schema

#### [NEW] `lib/schemas/udm_schema.json`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HWPX Unified Document Model",
  "type": "object",
  "properties": {
    "document_metadata": {
      "title": "string",
      "author": "string",
      "created_at": "datetime"
    },
    "layout": {
      "page_width_mm": "number",
      "page_height_mm": "number",
      "columns": "integer",
      "border": {
        "type": "Solid|None|Dash",
        "width": "string",
        "color": "string"
      }
    },
    "content_structure": [
      {
        "section_index": "integer",
        "column_index": "integer",
        "paragraphs": [
          {
            "semantic_type": "Heading1|Heading2|BodyText|Answer|Equation|Caption",
            "text_content": "string",
            "runs": [
              {
                "text": "string",
                "style": {
                  "font_family": "string",
                  "font_size_pt": "number",
                  "is_bold": "boolean",
                  "color_hex": "#RRGGBB"
                }
              }
            ],
            "controls": [
              {
                "type": "Table|Image|Equation",
                "properties": {},
                "data": {}
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

### Component 2: Reusable Action Templates

#### [NEW] `lib/templates/math_workbook.py`

**Purpose**: Pre-built action sequences for common math workbook patterns

| Template | Description |
|----------|-------------|
| `problem_header(num)` | 문제 번호 (e.g., "4.") with hanging indent |
| `subproblem(num)` | 소문제 번호 (e.g., "(1)") |
| `equation_inline(latex)` | 인라인 수식 |
| `answer_box(text)` | 정답 (Bold, larger font) |
| `two_column_layout()` | 2단 레이아웃 시작 |
| `column_break()` | 단 나누기 |
| `border_box_start()` | 테두리 박스 시작 |
| `border_box_end()` | 테두리 박스 종료 |

---

### Component 3: Missing HwpAction Models

#### [MODIFY] `lib/models.py`

| Action | Status | Description |
|--------|--------|-------------|
| `BreakColumn` | ✓ 있음 | 단 나누기 |
| `MultiColumn` | ✓ 있음 | 다단 설정 |
| `CreateBorderBox` | ❌ 추가 필요 | 테두리 박스 생성 |
| `BreakPara` | ❌ 추가 필요 | 문단 나누기 (줄바꿈과 구분) |

New model:
```python
class CreateBorderBox(HwpAction):
    """전체 테두리 박스 (실선) 생성"""
    action_type: Literal["CreateBorderBox"] = "CreateBorderBox"
    border_type: str = Field("Solid", description="Border style")
    border_width: str = Field("0.4mm", description="Border width")
    border_color: str = Field("#000000", description="Border color")
```

---

### Component 4: Fixed sample.pdf Action Sequence

#### [MODIFY] `output_actions.json` (Corrected Structure)

**Before** (현재 - 잘못됨):
```
4 → 5 → 6 → 7 → 8 → 9 (순차 나열, 레이아웃 무시)
```

**After** (수정 - 올바름):
```json
[
  // 1. 테두리 박스 시작
  {"action_type": "CreateBorderBox", "border_type": "Solid"},
  
  // 2. 2단 레이아웃 설정
  {"action_type": "MultiColumn", "count": 2, "same_size": true},
  
  // 3. 왼쪽 단: 문제 4, 5, 6
  {"action_type": "SetParaShape", ...},
  {"action_type": "InsertText", "text": "4. "},
  // ... 문제 4, 5, 6 ...
  
  // 4. 단 나누기
  {"action_type": "BreakColumn"},
  
  // 5. 오른쪽 단: 문제 7, 8, 9
  {"action_type": "InsertText", "text": "7. "},
  // ... 문제 7, 8, 9 ...
  
  // 6. 2단 종료 (1단으로 복귀)
  {"action_type": "MultiColumn", "count": 1}
]
```

---

## Verification Plan

### Automated Tests
1. `test_templates.py`: Math workbook template generation
2. `test_udm_schema.py`: JSON schema validation
3. `test_two_column.py`: Column break placement

### Manual Verification
1. Generate `sample_fixed.hwpx` with corrected actions
2. Open in HWP 2024 and verify 2-column layout

---

## Files to Create/Modify

| Action | Path | Description |
|--------|------|-------------|
| [NEW] | `lib/schemas/udm_schema.json` | UDM JSON Schema |
| [NEW] | `lib/templates/math_workbook.py` | Reusable action templates |
| [MODIFY] | `lib/models.py` | Add `CreateBorderBox`, `BreakPara` |
| [NEW] | `output_actions_fixed.json` | Corrected sample.pdf actions |
| [MODIFY] | `lib/owpml/document_builder.py` | Support new actions |

