# mathpix.md v2.0 수정안 통합 문서

> **Version:** 1.0 | **Status:** READY FOR REVIEW | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction
> **Source Templates:** T1, T2, T3, T4

---

## Overview

| Item | Value |
|------|-------|
| Total Modifications | 9 sections |
| Major Rewrites | 2 (Stage B, Stage C) |
| Updates | 3 (Stage D, Stage E, Human Review) |
| New Sections | 3 (Test Strategy, Threshold Config, YOLO Training) |
| Schema Version | 1.0.0 → 2.0.0 |

## Modification Summary

```
mathpix.md v2.0 변경 요약
├── [MAJOR REWRITE] Section 3.B: Text Parse (lines 149-200)
│   └── Source: Template 2 (Mathpix API Integration)
├── [MAJOR REWRITE] Section 3.C: Vision Parse (lines 203-262)
│   └── Source: Template 1 (YOLO + Claude Hybrid)
├── [UPDATE] Section 3.D: Alignment (lines 275-328)
│   └── Source: Template 4 (Threshold Calibration)
├── [UPDATE] Section 3.E: Semantic Graph (lines 332-398)
│   └── Source: Template 4 (Threshold Calibration)
├── [UPDATE] Section 5: Human Review (lines 956-1112)
│   └── Source: Template 4 (Threshold Calibration)
├── [NEW] Section 7: Test Strategy
│   └── Source: Template 3 (Test Framework Design)
├── [NEW] Section 8: Threshold Configuration
│   └── Source: Template 4 (Threshold Calibration)
└── [NEW] Section 9: YOLO Training Specification
    └── Source: Template 1 (Claude Vision Alternative)
```

---

## 1. Section 3.B: Text Parse (MAJOR REWRITE)

### Current State (v1.0) - Lines 149-200
```json
{
  "text_spec": {
    "mathpix_response": {
      "latex_styled": "...",
      "confidence": 0.92,
      "is_handwritten": false
    }
    // detection_map, line_data 미사용
  }
}
```

### Gap Analysis
| Missing Field | Source | Impact |
|---------------|--------|--------|
| `detection_map` | Mathpix API v3 | Stage C 트리거 불가 |
| `content_flags` | detection_map 변환 | 콘텐츠 타입 판별 불가 |
| `line_segments` | line_data | 요소별 상세 위치 정보 누락 |
| `vision_parse_triggers` | - | Stage C 필요성 판단 불가 |
| `writing_style` | is_handwritten 확장 | 필기 감지 정밀도 저하 |

### Proposed Schema v2.0.0

```json
{
  "text_spec": {
    "schema_version": "2.0.0",
    "image_id": "img_001",

    "mathpix_raw": {
      "latex_styled": "f(x) = x^2 + 2x + 1",
      "text": "다음 함수의 그래프를 그리시오. f(x) = x² + 2x + 1",
      "confidence": 0.92,
      "detection_map": {
        "contains_diagram": 1,
        "contains_chart": 0,
        "contains_table": 0,
        "contains_graph": 1,
        "contains_geometry": 1,
        "is_inverted": 0,
        "is_text_only": 0
      },
      "line_data": [
        {
          "type": "text",
          "text": "다음 함수의 그래프를 그리시오.",
          "cnt": [[50,50], [450,50], [450,80], [50,80]],
          "confidence": 0.98
        },
        {
          "type": "equation",
          "latex": "f(x) = x^2 + 2x + 1",
          "cnt": [[50,100], [350,100], [350,145], [50,145]],
          "confidence": 0.94
        }
      ]
    },

    "content_flags": {
      "contains_diagram": true,
      "contains_chart": false,
      "contains_table": false,
      "contains_graph": true,
      "contains_geometry": true,
      "is_text_only": false,
      "is_inverted": false
    },

    "vision_parse_triggers": ["DIAGRAM_EXTRACTION", "GRAPH_ANALYSIS", "GEOMETRIC_FIGURE_PARSING"],
    "vision_parse_required": true,

    "line_segments": [
      {
        "id": "seg_001",
        "type": "text",
        "content": "다음 함수의 그래프를 그리시오.",
        "bbox": {"x": 50, "y": 50, "width": 400, "height": 30},
        "confidence": 0.98,
        "source_contour": [[50,50], [450,50], [450,80], [50,80]]
      },
      {
        "id": "seg_002",
        "type": "equation",
        "content_latex": "f(x) = x^2 + 2x + 1",
        "bbox": {"x": 50, "y": 100, "width": 300, "height": 45},
        "confidence": 0.94,
        "source_contour": [[50,100], [350,100], [350,145], [50,145]]
      }
    ],

    "writing_style": "printed",

    "extracted_elements": [
      {
        "id": "elem_001",
        "type": "equation",
        "content_latex": "f(x) = x^2 + 2x + 1",
        "bbox": {"x": 50, "y": 100, "width": 300, "height": 45},
        "confidence": 0.94,
        "provenance": "mathpix_api_v3",
        "line_segment_ref": "seg_002",
        "review_required": false
      },
      {
        "id": "elem_002",
        "type": "text",
        "content": "다음 함수의 그래프를 그리시오.",
        "bbox": {"x": 50, "y": 50, "width": 400, "height": 30},
        "confidence": 0.98,
        "provenance": "mathpix_api_v3",
        "line_segment_ref": "seg_001",
        "review_required": false
      }
    ],

    "uncertainty": {
      "overall_confidence": 0.95,
      "low_confidence_elements": [],
      "vision_parse_confidence_penalty": 0.0
    },

    "review_required": false
  }
}
```

### Stage C Trigger Logic (New)

```python
def should_trigger_vision_parse(text_spec):
    """detection_map → Stage C 트리거 결정"""
    dm = text_spec.get("content_flags", {})
    triggers = []

    if dm.get("contains_diagram"):
        triggers.append("DIAGRAM_EXTRACTION")
    if dm.get("contains_chart"):
        triggers.append("CHART_DIGITIZATION")
    if dm.get("contains_graph"):
        triggers.append("GRAPH_ANALYSIS")
    if dm.get("contains_geometry"):
        triggers.append("GEOMETRIC_FIGURE_PARSING")

    return len(triggers) > 0, triggers
```

### Coordinate Transform (New)

```python
def contour_to_bbox(contour):
    """line_data.cnt → internal bbox format"""
    xs = [pt[0] for pt in contour]
    ys = [pt[1] for pt in contour]
    return {
        "x": min(xs),
        "y": min(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys)
    }
```

---

## 2. Section 3.C: Vision Parse (MAJOR REWRITE)

### Current State (v1.0) - Lines 203-262

**CRITICAL FLAW:** 현재 설계는 Claude Vision이 정확한 bbox를 생성할 수 있다고 가정
```json
// INVALID ASSUMPTION
"bbox": {"x": 60, "y": 170, "width": 380, "height": 280}  // Claude cannot produce this reliably
```

### Gap Analysis

| Issue | Severity | Impact |
|-------|----------|--------|
| Claude Vision bbox 불가 | **CRITICAL** | Stage C 전체 구현 불가 |
| 픽셀 수준 정밀도 필요 | HIGH | 좌표계 정합성 실패 |
| 단일 모델 의존 | MEDIUM | 실패 시 대안 없음 |

### Proposed Architecture: YOLO + Claude Hybrid

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
│  - pixel accuracy   │     │  - context meaning   │
└─────────┬───────────┘     └─────────┬───────────┘
          │                           │
          └──────────────┬────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  MERGE & ALIGN                                          │
│  - Match YOLO boxes with Claude labels                  │
│  - combined_confidence = f(yolo_conf, claude_conf)      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  OUTPUT: diagram_candidates (v2.0.0)                    │
└─────────────────────────────────────────────────────────┘
```

### Proposed Schema v2.0.0

```json
{
  "vision_spec": {
    "schema_version": "2.0.0",
    "image_id": "img_001",
    "processing_mode": "yolo_claude_hybrid",

    "detection_layer": {
      "model": "yolo26-math-v1",
      "model_version": "1.0.0",
      "inference_time_ms": 45,
      "elements": [
        {
          "id": "det_001",
          "class": "coordinate_axis",
          "bbox": {"coordinates": [60, 170, 440, 450], "format": "xyxy"},
          "detection_confidence": 0.94
        },
        {
          "id": "det_002",
          "class": "curve_parabola",
          "bbox": {"coordinates": [80, 200, 400, 420], "format": "xyxy"},
          "detection_confidence": 0.87
        },
        {
          "id": "det_003",
          "class": "point_label",
          "bbox": {"coordinates": [120, 380, 150, 410], "format": "xyxy"},
          "detection_confidence": 0.91
        },
        {
          "id": "det_004",
          "class": "point_label",
          "bbox": {"coordinates": [200, 350, 230, 380], "format": "xyxy"},
          "detection_confidence": 0.89
        }
      ]
    },

    "interpretation_layer": {
      "model": "claude-opus-4-5",
      "model_version": "20251101",
      "elements": [
        {
          "detection_ref": "det_001",
          "semantic_type": "cartesian_coordinate_system",
          "interpretation": {
            "x_axis_label": "x",
            "y_axis_label": "y",
            "origin_visible": true,
            "grid_present": false
          },
          "interpretation_confidence": 0.92
        },
        {
          "detection_ref": "det_002",
          "semantic_type": "parabola_curve",
          "interpretation": {
            "inferred_equation": "y = x^2 + 2x + 1",
            "opening_direction": "upward",
            "vertex_region": "left_of_origin"
          },
          "interpretation_confidence": 0.88
        },
        {
          "detection_ref": "det_003",
          "semantic_type": "labeled_point",
          "interpretation": {
            "label": "vertex",
            "meaning": "꼭짓점",
            "coords_inferred": [-1, 0]
          },
          "interpretation_confidence": 0.85
        },
        {
          "detection_ref": "det_004",
          "semantic_type": "labeled_point",
          "interpretation": {
            "label": "y-intercept",
            "meaning": "y절편",
            "coords_inferred": [0, 1]
          },
          "interpretation_confidence": 0.90
        }
      ],
      "relationships": [
        {
          "type": "point_on_curve",
          "subject": "det_003",
          "object": "det_002",
          "confidence": 0.87
        },
        {
          "type": "point_on_curve",
          "subject": "det_004",
          "object": "det_002",
          "confidence": 0.91
        }
      ]
    },

    "merged_output": {
      "diagram_candidates": [
        {
          "id": "diag_001",
          "diagram_type": "function_graph",
          "bbox_source": "yolo26",
          "label_source": "claude",
          "combined_confidence": 0.89,
          "bbox": {"x": 60, "y": 170, "width": 380, "height": 280},
          "detected_elements": {
            "coordinate_system": {
              "type": "cartesian_2d",
              "x_axis": {"visible": true, "label": "x", "range_inferred": [-3, 5]},
              "y_axis": {"visible": true, "label": "y", "range_inferred": [-2, 10]},
              "source": {"bbox": "yolo26", "semantics": "claude"}
            },
            "curves": [
              {
                "id": "curve_001",
                "type": "parabola",
                "inferred_equation": "y = x^2 + 2x + 1",
                "bbox": {"coordinates": [80, 200, 400, 420], "format": "xyxy", "source": "yolo26"},
                "key_points": [
                  {"type": "vertex", "coords": [-1, 0], "confidence": 0.85, "source": "claude"},
                  {"type": "y_intercept", "coords": [0, 1], "confidence": 0.90, "source": "claude"}
                ],
                "asserted": false,
                "inferred": true,
                "combined_confidence": 0.87
              }
            ],
            "labels": [
              {
                "text": "f(x)",
                "bbox": {"coordinates": [350, 250, 380, 280], "format": "xyxy", "source": "yolo26"},
                "position_inferred": [2, 5],
                "confidence": 0.88
              }
            ]
          },
          "provenance": {
            "detection": "yolo26-math-v1",
            "interpretation": "claude-opus-4-5",
            "merge_strategy": "confidence_weighted"
          },
          "uncertainty": 0.11,
          "review_required": false,
          "review_severity": null,
          "evidence_refs": ["img_001:bbox(60,170,440,450)"]
        }
      ]
    },

    "fallback_used": false,
    "fallback_reason": null
  }
}
```

### Fallback Strategy

```
Primary: YOLO26 → Claude Opus 4.5
    ↓ (YOLO confidence < 0.5 또는 실패 시)
Fallback 1: Gemini 2.5 Pro (zero-shot bbox + interpretation)
    ↓ (Gemini 실패 시)
Fallback 2: Claude-only (semantic description without precise bbox)
    ↓ (낮은 confidence)
Fallback 3: Manual annotation required (Stage G 즉시 진입)
    → review_required: true, review_severity: "blocker"
```

### Combined Confidence Calculation

```python
def calculate_combined_confidence(yolo_conf, claude_conf, element_type):
    """요소 타입별 가중치를 적용한 신뢰도 계산"""
    weights = {
        "coordinate_system": {"yolo": 0.7, "claude": 0.3},
        "curve": {"yolo": 0.5, "claude": 0.5},
        "point_label": {"yolo": 0.6, "claude": 0.4},
        "labeled_region": {"yolo": 0.8, "claude": 0.2}
    }

    w = weights.get(element_type, {"yolo": 0.5, "claude": 0.5})
    return (yolo_conf * w["yolo"]) + (claude_conf * w["claude"])
```

---

## 3. Section 3.D: Alignment (UPDATE)

### Changes from Template 4

**Add:** Element-type specific threshold application

```json
{
  "alignment_report": {
    "threshold_config_applied": "v2.0.0",
    "matched_pairs": [
      {
        "text_element": "elem_001",
        "diagram_element": "curve_001",
        "match_type": "equation_to_curve",
        "consistency_score": 0.92,
        "element_threshold": 0.75,
        "threshold_passed": true,
        "discrepancies": []
      }
    ]
  },
  "inconsistencies": [
    {
      "id": "incon_001",
      "type": "coefficient_mismatch",
      "severity_threshold": 0.80,
      "current_confidence": 0.72,
      "review_required": true,
      "review_severity": "high",
      "severity_auto_assigned": true,
      "severity_reason": "confidence(0.72) < threshold(0.80) for inconsistency type"
    }
  ]
}
```

---

## 4. Section 5: Human Review (UPDATE)

### Changes from Template 4

**Add:** Dynamic threshold-based severity assignment

| Element Type | Base Threshold | Severity if Below |
|--------------|----------------|-------------------|
| `equation` | 0.70 | blocker |
| `curves` | 0.75 | blocker |
| `inconsistency` | 0.80 | blocker |
| `points` | 0.65 | high |
| `diagram_type` | 0.60 | high |
| `alignment_match` | 0.60 | high |
| `labels` | 0.55 | medium |
| `text` | 0.45 | medium |
| `bbox` | 0.40 | low |

**Add:** Operating Point Targets

```yaml
operating_targets:
  critical_elements:  # equation, curves, inconsistency
    recall_target: 0.98
    precision_target: 0.60
    rationale: "오류 놓치지 않기 최우선"
  high_elements:      # points, diagram_type, alignment
    recall_target: 0.95
    precision_target: 0.70
  medium_elements:    # labels, text
    recall_target: 0.90
    precision_target: 0.75
  low_elements:       # bbox
    recall_target: 0.85
    precision_target: 0.80
```

---

## 5. Section 7: Test Strategy (NEW)

### Golden Dataset Structure

```
datasets/golden/
├── manifest.yaml                    # 버전 및 메타데이터
├── ground_truth/
│   ├── elementary/                  # 초등 (55 samples)
│   │   ├── arithmetic/
│   │   └── geometry_2d/
│   ├── middle_school/               # 중등 (75 samples)
│   │   ├── algebra_basic/
│   │   └── functions_linear/
│   ├── high_school/                 # 고등 (120 samples)
│   │   ├── functions_advanced/
│   │   ├── trigonometry/
│   │   └── calculus_intro/
│   └── edge_cases/                  # 엣지 케이스 (40 samples)
│       ├── handwritten/
│       ├── low_quality/
│       └── ambiguous/
└── annotations/
    └── {problem_id}_annotation.json
```

### Stage-Level Metrics

| Stage | Primary Metric | Threshold | Secondary Metrics |
|-------|----------------|-----------|-------------------|
| A. Ingestion | quality_score | ≥ 0.6 | blur_score, resolution |
| B. TextParse | CER | < 0.05 | latex_structural_match ≥ 0.9 |
| C. VisionParse | bbox_iou | ≥ 0.7 | label_recall ≥ 0.85 |
| D. Alignment | alignment_f1 | ≥ 0.85 | blocker_accuracy ≥ 0.95 |
| E. SemanticGraph | node_accuracy | ≥ 0.9 | edge_accuracy ≥ 0.85 |
| F. Regeneration | param_accuracy | ≥ 0.95 | export_valid = true |
| G. HumanReview | false_positive_rate | < 0.1 | review_time_avg |
| H. Export | completeness_score | ≥ 0.95 | format_valid = true |

### CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  Smoke Tests (매 커밋)                                   │
│  - 5개 대표 샘플                                         │
│  - 실행 시간: < 60초                                     │
│  - 통과 기준: 100%                                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Full Regression (야간)                                  │
│  - 250+ 전체 샘플                                        │
│  - 실행 시간: < 30분                                     │
│  - 통과 기준: overall ≥ 90%, per-stage ≥ 85%            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Canary Testing (릴리즈)                                 │
│  - 5% → 10% → 25% → 50% → 100% 점진 배포                │
│  - 회귀 임계값: 2% pass rate 하락 시 중단               │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Section 8: Threshold Configuration (NEW)

### Full Configuration Schema

```yaml
# config/threshold_calibration.yaml
version: "2.0.0"

global_settings:
  min_threshold: 0.15
  max_threshold: 0.90
  learning_rate: 0.08
  feedback_window_size: 100

targets:
  false_negative_rate: 0.05
  false_positive_rate: 0.30

element_thresholds:
  # CRITICAL risk (Recall ≥ 0.98)
  equation:
    base: 0.70
    risk: critical
    default_severity: blocker
  curves:
    base: 0.75
    risk: critical
    default_severity: blocker
  inconsistency:
    base: 0.80
    risk: critical
    default_severity: blocker

  # HIGH risk (Recall ≥ 0.95)
  points:
    base: 0.65
    risk: high
    default_severity: high
  diagram_type:
    base: 0.60
    risk: high
    default_severity: high
  alignment_match:
    base: 0.60
    risk: high
    default_severity: high
  node:
    base: 0.60
    risk: high
    default_severity: high

  # MEDIUM risk (Recall ≥ 0.90)
  labels:
    base: 0.55
    risk: medium_high
    default_severity: medium
  edge:
    base: 0.55
    risk: medium
    default_severity: medium
  text:
    base: 0.45
    risk: medium
    default_severity: medium

  # LOW risk (Recall ≥ 0.85)
  bbox:
    base: 0.40
    risk: low
    default_severity: low

context_modifiers:
  image_quality:
    formula: "0.85 + (quality_score * 0.15)"
  complexity:
    elementary: 1.05
    middle_school: 1.00
    high_school: 0.95
    advanced: 0.90
  element_density:
    formula: "1.0 - (min(element_count, 10) * 0.01)"

feedback_loop:
  fn_rate_trigger: 0.05
  fn_adjustment: -0.08
  fp_rate_trigger: 0.30
  fp_adjustment: 0.04

hard_rules:
  - condition: "confidence < 0.2"
    action: "ALWAYS_REVIEW"
    severity: blocker
  - condition: "diagram_type == 'unknown'"
    action: "ALWAYS_REVIEW"
    severity: high
  - condition: "coordinate_system == 'ambiguous'"
    action: "ALWAYS_REVIEW"
    severity: high
  - condition: "blocker_count > 0"
    action: "HALT_PIPELINE"

monitoring:
  false_negative_rate:
    target: 0.05
    warning: 0.07
    critical: 0.10
  false_positive_rate:
    target: 0.30
    warning: 0.40
    critical: 0.50
  review_queue_depth:
    target: 200
    warning: 300
    critical: 500
  confidence_drift_kl:
    target: 0.10
    warning: 0.15
    critical: 0.25

calibration_schedule:
  initial: "Golden Dataset sweep"
  weekly: "Reviewer feedback analysis"
  monthly: "Drift detection (>5% triggers recalibration)"
  quarterly: "Full recalibration + operating point review"
```

### Dynamic Threshold Algorithm

```python
def compute_effective_threshold(element_type, context, feedback_stats):
    """3-Layer 동적 threshold 계산"""
    # Layer 1: Base threshold
    base = BASE_THRESHOLDS[element_type]

    # Layer 2: Context modifiers
    quality_mod = 0.85 + (context.image_quality_score * 0.15)
    complexity_mod = COMPLEXITY_MODS[context.problem_level]
    density_mod = 1.0 - (min(context.element_count, 10) * 0.01)
    context_modifier = quality_mod * complexity_mod * density_mod

    # Layer 3: Feedback loop
    fn_rate = feedback_stats.false_negative_rate
    fp_rate = feedback_stats.false_positive_rate

    if fn_rate > 0.05:
        feedback_mod = 1.0 - ((fn_rate - 0.05) * 0.08)
    elif fp_rate > 0.30:
        feedback_mod = 1.0 + ((fp_rate - 0.30) * 0.04)
    else:
        feedback_mod = 1.0

    return clamp(base * context_modifier * feedback_mod, 0.15, 0.90)
```

---

## 7. Section 9: YOLO Training Specification (NEW)

### Dataset Requirements

| Element Type | Min Samples | Label Format | Priority |
|--------------|-------------|--------------|----------|
| Point labels (P, Q, A, B) | 500 | `point_label` | HIGH |
| Curves (parabola, sine, etc.) | 400 | `curve_{type}` | HIGH |
| Line segments | 300 | `line_segment` | MEDIUM |
| Axes (x, y) | 200 | `axis_{orientation}` | MEDIUM |
| Shaded regions | 200 | `shaded_region` | MEDIUM |
| Angle markers | 150 | `angle_marker` | LOW |
| **Total** | **1750** | - | - |

### Annotation Format (YOLO v8)

```yaml
# Example: math_diagram_001.txt
# class_id center_x center_y width height
0 0.45 0.32 0.12 0.08   # point_label
1 0.50 0.55 0.60 0.40   # curve_parabola
2 0.50 0.85 0.80 0.02   # axis_x
3 0.15 0.50 0.02 0.70   # axis_y
```

### Class Mapping

```yaml
# classes.yaml
names:
  0: point_label
  1: curve_parabola
  2: curve_sine
  3: curve_cosine
  4: curve_linear
  5: curve_exponential
  6: axis_x
  7: axis_y
  8: line_segment
  9: shaded_region
  10: angle_marker
  11: coordinate_grid
  12: function_label
```

### Training Configuration

```yaml
# yolo_math_config.yaml
model: yolov8m  # medium model for balance
imgsz: 640
epochs: 100
batch: 16
patience: 20
optimizer: AdamW
lr0: 0.001
lrf: 0.01
augment:
  hsv_h: 0.015
  hsv_s: 0.4
  hsv_v: 0.4
  degrees: 5
  translate: 0.1
  scale: 0.3
  flipud: 0.0  # No vertical flip for math
  fliplr: 0.0  # No horizontal flip for math
  mosaic: 0.5
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Threshold configuration YAML 작성
- [ ] Pydantic 스키마 v2.0.0 구현
- [ ] text_spec, vision_spec 모델 정의

### Phase 2A: Stage B (Week 2-3)
- [ ] Mathpix API 클라이언트 확장
- [ ] detection_map → content_flags 변환
- [ ] line_data → line_segments 변환
- [ ] Stage C 트리거 로직 구현

### Phase 2B: Stage C (Week 2-3)
- [ ] YOLO 학습 데이터 수집 시작
- [ ] Hybrid merger 구현
- [ ] Fallback strategy 구현
- [ ] combined_confidence 계산

### Phase 3: Testing (Week 4-5)
- [ ] Golden Dataset 50 샘플 구축
- [ ] Smoke 테스트 구현
- [ ] CI 워크플로우 설정

### Phase 4: Integration (Week 6)
- [ ] mathpix.md v2.0 최종 병합
- [ ] E2E 테스트 실행
- [ ] 문서화 완료

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:
1. Read this file: `.agent/plans/mathpix_v2_modifications.md`
2. Check Template files for detailed designs
3. Implementation status in TodoWrite
4. Current phase in Implementation Checklist

---

> **This document is the master reference for mathpix.md v2.0 modifications.**
> All changes are traceable to source Templates (T1-T4).
