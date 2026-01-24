# Template 2: Mathpix API 통합 상세 설계

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | HIGH |
| Total Tasks | 5 |
| Schema Changes | text_spec v1.0 → v2.0.0 |
| New Fields | 12+ (detection_map, line_data, contour, etc.) |

## Problem Statement

**현재 설계의 Gap:**
1. `latex_styled`, `confidence` 필드만 사용 - API가 제공하는 정보의 20%만 활용
2. `detection_map` 미활용 - Stage C 트리거 로직 부재
3. bbox 형식 불일치: 설계 `{x, y, width, height}` vs API `{top_left_x, top_left_y, width, height}`
4. `line_data` 미활용 - 요소별 상세 정보 누락

## Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Research | Mathpix API v3 전체 스키마 문서화 | COMPLETED |
| 2 | Design | Field Mapping Table 작성 | COMPLETED |
| 3 | Design | detection_map 활용 전략 수립 | COMPLETED |
| 4 | Design | text_spec v2.0.0 스키마 설계 | COMPLETED |
| 5 | Config | MCP 서버 설정 예시 작성 | COMPLETED |

## Key Findings

### 1. Mathpix API 주요 응답 필드

| 필드 | 용도 | 현재 활용 |
|------|------|----------|
| `latex_styled` | LaTeX 수식 | ✅ 사용 중 |
| `confidence` | 전체 신뢰도 | ✅ 사용 중 |
| `detection_map` | 콘텐츠 타입 감지 | ❌ 미사용 |
| `position` | bbox 좌표 | ❌ 미사용 |
| `line_data` | 요소별 상세 | ❌ 미사용 |
| `is_handwritten` | 필기 감지 | ❌ 미사용 |

### 2. detection_map → Stage C 트리거 전략

```python
def should_trigger_vision_parse(detection_map):
    reasons = []
    if detection_map.get("contains_diagram") == 1:
        reasons.append("DIAGRAM_EXTRACTION")
    if detection_map.get("contains_chart") == 1:
        reasons.append("CHART_DIGITIZATION")
    if detection_map.get("contains_graph") == 1:
        reasons.append("GRAPH_ANALYSIS")
    if detection_map.get("contains_geometry") == 1:
        reasons.append("GEOMETRIC_FIGURE_PARSING")
    return len(reasons) > 0, reasons
```

### 3. 좌표 변환 로직

```python
# Mathpix → Internal
def transform_position_to_bbox(position):
    return {
        "x": position["top_left_x"],
        "y": position["top_left_y"],
        "width": position["width"],
        "height": position["height"]
    }

# Contour → BBox (line_data.cnt 변환)
def contour_to_bbox(contour):
    xs = [pt[0] for pt in contour]
    ys = [pt[1] for pt in contour]
    return {
        "x": min(xs),
        "y": min(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys)
    }
```

## text_spec Schema v2.0.0 (Summary)

### 신규 필드

| 필드 | 타입 | 용도 |
|------|------|------|
| `content_flags` | object | detection_map 기반 콘텐츠 플래그 |
| `content_flags.contains_diagram` | boolean | Stage C 트리거 |
| `content_flags.contains_graph` | boolean | Stage C 트리거 |
| `line_segments` | array | line_data 기반 요소별 상세 |
| `vision_parse_triggers` | array | Stage C 트리거 이유 목록 |
| `writing_style` | enum | "printed" \| "handwritten" \| "mixed" |

### content_flags 구조

```json
{
  "content_flags": {
    "contains_diagram": true,
    "contains_chart": false,
    "contains_table": false,
    "contains_graph": true,
    "contains_geometry": true,
    "is_text_only": false,
    "is_inverted": false
  }
}
```

## MCP Server Configuration

```json
{
  "mcpServers": {
    "mathpix": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-fetch"],
      "env": {
        "MATHPIX_APP_ID": "${MATHPIX_APP_ID}",
        "MATHPIX_APP_KEY": "${MATHPIX_APP_KEY}"
      },
      "config": {
        "baseUrl": "https://api.mathpix.com/v3",
        "endpoints": {
          "text": {
            "path": "/text",
            "method": "POST",
            "defaultOptions": {
              "formats": ["latex_styled", "text"],
              "data_options": {
                "include_line_data": true,
                "include_diagram_text": true
              }
            }
          }
        },
        "rateLimit": {
          "requestsPerMinute": 60,
          "requestsPerDay": 5000
        },
        "retry": {
          "maxAttempts": 3,
          "baseDelayMs": 1000
        }
      }
    }
  }
}
```

## Error Handling Strategy

| 에러 유형 | HTTP 코드 | 복구 전략 |
|----------|----------|----------|
| Rate Limit | 429 | Exponential backoff (1s→2s→4s) |
| Timeout | 408, 504 | 작은 영역으로 재시도 |
| Invalid Image | 400 | review_required=true, Stage G 진입 |
| Server Error | 500-503 | 3회 재시도 후 circuit breaker |
| Low Confidence | 200 (conf<0.5) | Stage C fallback 트리거 |

## Quick Resume After Auto-Compact

If context is compacted, resume by:
1. Read this file: `.agent/plans/template_2_mathpix_api_integration.md`
2. Key decisions already made:
   - text_spec v2.0.0 with content_flags
   - detection_map → Stage C trigger logic defined
   - Coordinate transform functions specified
3. Next: mathpix.md Stage B 섹션 업데이트

## Agent Registry

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| API Integration Design | a7b9c86 | completed | No |

## Sources

- [Mathpix API v3 Reference](https://docs.mathpix.com/)
- [Mathpix SuperNet Blog](https://mathpix.com/blog/supernet)
- [mpxpy Python Client](https://github.com/Mathpix/mpxpy)
