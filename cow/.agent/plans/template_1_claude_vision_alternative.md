# Template 1: Claude Vision 대체 아키텍처 연구

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | HIGH |
| Total Tasks | 6 |
| Research Areas | 3 (Gemini, YOLO, Hybrid Architecture) |
| Schema Changes | Major (v2.0.0) |

## Problem Statement

**현재 설계의 치명적 결함:**
- `mathpix.md:231-246`에서 Claude Vision이 bbox 좌표를 반환한다고 가정
- **실제:** Claude Vision은 정확한 bounding box 생성 불가
- **영향:** Stage C (Vision Parse) 전체가 구현 불가능

## Research Findings

### Claude Vision의 한계 (확인됨)
- "Claude 3 models cannot provide the bounding box coordinates"
- 여러 번 테스트 시 bbox 좌표가 매번 다르게 반환
- 정밀한 좌표 추출이 필요한 작업에 부적합

### 대안 옵션 분석

| Option | 접근법 | 장점 | 단점 | 실현가능성 |
|--------|--------|------|------|-----------|
| **Option 1** | Gemini Vision | 단일 API, zero-shot | 좌표 불일치 가능, 벤더 종속 | HIGH |
| **Option 2** | YOLO + Claude | 정밀 좌표 + 의미 해석 | 학습 필요, 복잡성 | MEDIUM-HIGH |
| **Option 3** | 특수 CV 모델 + Claude | 도메인 최적화 | 파편화, 통합 복잡 | MEDIUM |

### 권장 아키텍처: Option 2 (YOLO + Claude Vision Hybrid)

**이유:**
1. YOLO → 픽셀 수준 정밀 bbox
2. Claude → 우수한 의미 해석 유지
3. 커스텀 학습으로 수학 다이어그램 특화 가능
4. 로컬 YOLO 추론으로 API 비용 절감

## Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Research | Gemini Vision bbox API 상세 조사 | PENDING |
| 2 | Research | YOLO26 수학 다이어그램 적용 가능성 검토 | PENDING |
| 3 | Design | Hybrid 아키텍처 데이터 흐름도 작성 | COMPLETED |
| 4 | Design | Stage C 스키마 v2.0.0 설계 | COMPLETED |
| 5 | Design | 기존 파이프라인 통합 포인트 정의 | COMPLETED |
| 6 | Document | mathpix.md Stage C 섹션 수정안 작성 | PENDING |

## Schema Changes (v2.0.0)

### 기존 스키마 (INVALID)
```json
{
  "bbox": [x1, y1, x2, y2]  // Claude가 생성 불가
}
```

### 신규 스키마 (Hybrid)
```json
{
  "detection_layer": {
    "model": "yolo26-math-v1",
    "elements": [{
      "bbox": {"coordinates": [120, 45, 280, 190], "format": "xyxy"},
      "detection_confidence": 0.92
    }]
  },
  "interpretation_layer": {
    "model": "claude-opus-4-5",
    "elements": [{
      "semantic_type": "labeled_point",
      "interpretation_confidence": 0.88
    }]
  },
  "merged_output": {
    "bbox_source": "yolo26",
    "label_source": "claude",
    "combined_confidence": 0.90
  }
}
```

## Data Flow (Hybrid Architecture)

```
┌─────────────────────────────────────────────────────────┐
│  INPUT: image + text_spec (from Stage B)                │
└─────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌─────────────────────┐     ┌─────────────────────┐
│  YOLO26 Detection   │     │  Claude Interpretation│
│  - bbox extraction  │     │  - semantic labels   │
│  - element classes  │     │  - relationships     │
└─────────┬───────────┘     └─────────┬───────────┘
          │                           │
          └──────────────┬────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  MERGE & ALIGN → diagram_candidates                     │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  OUTPUT → Stage D (Alignment & Consistency Check)       │
└─────────────────────────────────────────────────────────┘
```

## Implementation Phases

| Phase | 범위 | 예상 기간 |
|-------|------|----------|
| Phase 1 | Pretrained YOLO + Gemini (MVP) | 2주 |
| Phase 2 | Custom YOLO 학습 | 4주 |
| Phase 3 | Claude 통합 (Hybrid 완성) | 2주 |

## YOLO Training Dataset Requirements

| Element Type | 최소 샘플 수 | 라벨 포맷 |
|--------------|-------------|----------|
| Point labels (P, Q, A, B) | 500 | `point_label` |
| Line segments | 300 | `line_segment` |
| Curves (parabola, sine) | 400 | `curve_{type}` |
| Axes (x, y) | 200 | `axis_{orientation}` |
| Shaded regions | 200 | `shaded_region` |
| Angle markers | 150 | `angle_marker` |

## Fallback Strategy

```
Primary: YOLO26 → Claude Opus 4.5
    ↓ (YOLO 실패 시)
Fallback 1: Gemini 2.5 (zero-shot)
    ↓ (Gemini 실패 시)
Fallback 2: Manual annotation (Stage G 즉시 진입)
```

## Quick Resume After Auto-Compact

If context is compacted, resume by:
1. Read this file: `.agent/plans/template_1_claude_vision_alternative.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task
4. Key decision: **YOLO + Claude Hybrid architecture approved**

## Agent Registry

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Architecture Analysis | a90de04 | completed | No |

## Sources

- [Claude Vision Docs](https://platform.claude.com/docs/en/build-with-claude/vision)
- [Gemini Bounding Box](https://simonwillison.net/2024/Aug/26/gemini-bounding-box-visualization/)
- [YOLO26 Architecture](https://blog.roboflow.com/yolo26/)
- [Roboflow Claude 3 Analysis](https://blog.roboflow.com/claude-3-opus-multimodal/)
