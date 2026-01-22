# 수학 문제 이미지 파싱 파이프라인 설계

**Claude Native Vision 기반 재구성 가능한 구조화 데이터 생성을 위한 End-to-End Blueprint**

Human-in-the-loop 검토 체계를 핵심 설계 원칙으로 삼아, 수학 문제 이미지를 Desmos/GeoGebra 호환 형식으로 변환하는 전체 파이프라인을 제시한다. 이 보고서는 **Claude Opus 4.5** 모델과 **Claude Code v2.1.7**의 최신 기능을 최대한 활용하며, `review_required` 플래그 체계를 통해 불확실성이 높은 파싱 결과에 대한 사람의 검토를 보장한다.

**v2.0.0 (2026-01-18):** 3-layer 동적 threshold 시스템 도입 - Base → Context → Feedback 아키텍처로 element type별 적응형 threshold 적용.

---

## 1. 최신 Claude 모델 확정 (2026-01-14 기준)

### Claude Opus 4.5가 현재 최신 모델인 이유

Anthropic은 **2025년 11월 24일** Claude Opus 4.5를 공식 출시했으며, 이는 2026년 1월 현재 가장 최신의 Claude 모델이다. API 식별자는 `claude-opus-4-5-20251101`이며, Claude.ai 웹 인터페이스, Anthropic API, Amazon Bedrock, Google Cloud Vertex AI에서 사용 가능하다.

공식 발표에 따르면 Opus 4.5는 이전 버전(Opus 4.1) 대비 입출력 비용이 **67% 절감**되었으며($15/$75 → $5/$25 per million tokens), 동일한 200K 토큰 컨텍스트 윈도우를 유지하면서 vision 성능이 개선되었다.

### Native Vision 기능 상세

| 항목 | 사양 |
|------|------|
| **최대 이미지 수** | API 요청당 **100장**, Claude.ai에서 **20장** |
| **최대 해상도** | **8000×8000 픽셀** (단일 이미지) |
| **20장 초과 시** | 2000×2000 픽셀로 제한 |
| **지원 포맷** | JPEG, PNG, GIF, WebP |
| **토큰 계산** | `(width × height) / 750` |
| **Tool-use 호환** | **지원** (Vision + Tool 동시 사용 가능) |
| **입력 방식** | Base64 인코딩, URL 참조, Files API |

Vision 처리 시 **이미지를 텍스트보다 먼저 배치**하는 것이 최적 성능을 위해 권장되며, 1568픽셀 이하의 장변을 가진 이미지는 리사이징 없이 처리된다. 이 사양은 수학 문제 이미지 파싱에 충분한 해상도와 다중 이미지 처리 능력을 제공한다.

### 알려진 제약 사항

Claude Vision은 **공간 추론(spatial reasoning)**에서 제한적 정확도를 보이며, 정밀한 좌표 추출이나 복잡한 레이아웃 분석에서 불확실성이 발생할 수 있다. 또한 200픽셀 미만의 소형 이미지, 회전된 이미지, 저품질 스캔에서 hallucination 가능성이 있어 `review_required` 플래그 체계가 필수적이다.

**공식 문서 출처:**
- Vision 문서: https://platform.claude.com/docs/en/build-with-claude/vision
- 모델 개요: https://docs.anthropic.com/en/docs/about-claude/models
- Opus 4.5 발표: https://www.anthropic.com/news/claude-opus-4-5

---

## 2. Claude Code v2.1.7 CHANGELOG 및 기능 활용 설계

### a) Feature Inventory (≤ v2.1.7)

**CHANGELOG 공식 출처:**
- GitHub: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- 공식 문서: https://code.claude.com/docs/en/changelog

| 기능 | 옵션/플래그 | 제약 | 권장 설정 |
|------|------------|------|----------|
| **Image 지원** | Drag-drop, Cmd+V (iTerm2) | JPEG/PNG/GIF/WebP | 100KB 이하 JPEG 권장 |
| **JSON 출력** | `--output-format json` | stream-json 가능 | 파이프라인 통합 시 json |
| **Headless 모드** | `-p "prompt"` | 인터랙티브 불가 | 자동화 배치 처리용 |
| **Hook 시스템** | PreToolUse, PostToolUse, Stop | Custom hook 정의 가능 | 검증 단계에 활용 |
| **Skills 시스템** | ~/.claude/skills/ | Hot-reload 지원 | 파싱 규칙 모듈화 |
| **Background Agents** | `&` prefix, Ctrl+B | Context 격리됨 | 병렬 파싱 작업용 |
| **Context 관리** | `/compact`, `/context` | 200K 토큰 제한 | 대형 이미지셋 처리 시 compact |
| **Model 선택** | `--model opus` | opus, sonnet, haiku | opus (정확도 우선) |
| **Tool 제한** | `--tools ['Read', 'Bash']` | Built-in tools만 | 필요 도구만 활성화 |
| **MCP 통합** | `--mcp-config file.json` | 다중 config 가능 | 외부 API 연결용 |
| **Plugin 시스템** | v2.0.12+ | Marketplace 지원 | Custom agents 정의 |
| **Fork Context** | `context: fork` in skills | Sub-agent 격리 | 독립 파싱 태스크 |

### b) Pipeline Impact Mapping

| 파이프라인 단계 | 활용 기능 | 적용 방식 |
|----------------|----------|----------|
| **A. Ingestion** | Image 지원, `--output-format json` | 이미지 메타데이터 추출을 JSON으로 출력 |
| **B. Text Parse** | MCP 통합 | Mathpix API를 MCP server로 연결 |
| **C. Vision Parse** | Skills 시스템, Fork Context | 도형/그래프 파싱 규칙을 skill로 모듈화 |
| **D. Alignment** | Hook 시스템 (PreToolUse) | 정합성 검증 로직을 hook으로 구현 |
| **E. Semantic Graph** | Background Agents | 병렬 관계 추론 작업 |
| **F. Regeneration** | JSON 출력, Tool 제한 | Desmos/GeoGebra spec 생성 |
| **G. Human Review** | `/context` 명령 | 토큰 사용량 모니터링으로 검토 우선순위 결정 |
| **H. Export** | Headless 모드 | 배치 DOCX 생성 자동화 |

### c) Enablement Plan

| 기능 | 기본값 | 활성화 플래그 | 실패 시 Fallback |
|------|--------|--------------|-----------------|
| **JSON 출력** | text | `--output-format json` | text 파싱 후 수동 JSON 변환 |
| **Opus 모델** | sonnet | `--model opus` | sonnet으로 재시도 후 review_required |
| **Hook 시스템** | 비활성 | `.claude/hooks/` 디렉토리 | 수동 검증 단계 추가 |
| **Skills** | 비활성 | `~/.claude/skills/` 또는 프로젝트 내 | Inline prompt로 대체 |
| **MCP 서버** | 비활성 | `--mcp-config mathpix.json` | 직접 API 호출로 대체 |
| **Background** | 비활성 | `&` prefix 또는 Ctrl+B | Sequential 처리 |
| **Context Fork** | 비활성 | skill 내 `context: fork` | 동일 context에서 처리 |

---

## 3. 전체 파이프라인 설계도 (End-to-End Blueprint)

### 파이프라인 개요

```
[Image Input] → A.Ingestion → B.TextParse → C.VisionParse → D.Alignment
                                                               ↓
[Export] ← H.ExportSpec ← G.HumanReview ← F.Regeneration ← E.SemanticGraph
```

### A. Ingestion (이미지 수집 및 전처리)

**목적:** 입력 이미지의 메타데이터 추출 및 처리 가능 여부 사전 판단

**입력:** 단일/복수 이미지 파일 (JPEG, PNG, GIF, WebP)

**출력:**
```json
{
  "image_manifest": {
    "images": [
      {
        "id": "img_001",
        "filename": "problem_01.png",
        "dimensions": {"width": 1200, "height": 800},
        "format": "image/png",
        "file_size_kb": 85,
        "estimated_tokens": 1280
      }
    ],
    "total_images": 1,
    "total_estimated_tokens": 1280
  },
  "preflight_signals": {
    "resolution_adequate": true,
    "format_supported": true,
    "size_within_limit": true,
    "orientation_detected": "landscape",
    "quality_assessment": "acceptable",
    "review_required": false,
    "review_reason_code": null
  }
}
```

**실패 모드 및 가드레일:**
- 해상도 200px 미만 → `review_required: true`, `review_reason_code: "LOW_RESOLUTION"`
- 지원되지 않는 포맷 → 오류 반환, 변환 제안
- 8000px 초과 → 자동 리사이징 후 경고

**review_required 트리거:**
- 이미지 품질 평가 "poor" 이상
- 회전 감지된 경우
- 다중 페이지/복합 레이아웃 감지

---

### B. Text Parse (Mathpix 외부 처리)

**목적:** Mathpix API를 통한 수식 및 텍스트 OCR 결과 수신

**입력:** image_manifest의 이미지 참조

**출력:**
```json
{
  "text_spec": {
    "image_id": "img_001",
    "mathpix_response": {
      "latex_styled": "f(x) = x^2 + 2x + 1",
      "confidence": 0.92,
      "is_handwritten": false
    },
    "extracted_elements": [
      {
        "id": "elem_001",
        "type": "equation",
        "content_latex": "f(x) = x^2 + 2x + 1",
        "bbox": {"x": 50, "y": 120, "width": 300, "height": 45},
        "confidence": 0.92,
        "provenance": "mathpix_api_v3",
        "review_required": false
      },
      {
        "id": "elem_002",
        "type": "text",
        "content": "다음 함수의 그래프를 그리시오.",
        "bbox": {"x": 50, "y": 50, "width": 400, "height": 30},
        "confidence": 0.98,
        "provenance": "mathpix_api_v3",
        "review_required": false
      }
    ],
    "uncertainty": {
      "overall_confidence": 0.95,
      "low_confidence_elements": []
    },
    "review_required": false
  }
}
```

**실패 모드:**
- Mathpix API 응답 `image_unsupported_content` → 도형 전용 이미지로 표시
- Confidence 0.2 미만 → `review_required: true`

**데이터 계약 (B→C):**
- `text_spec.extracted_elements[]`의 `bbox` 좌표는 원본 이미지 픽셀 기준
- `content_latex`는 Mathpix Markdown 형식 (`\(...\)` 구분자)

---

### C. Vision Parse (Claude Vision 처리)

**목적:** 도형, 그래프, 레이아웃 요소 파싱 (Mathpix가 처리하지 못하는 영역)

**입력:** image_manifest + text_spec

**출력:**
```json
{
  "layout_blocks": [
    {
      "id": "block_001",
      "type": "problem_statement",
      "bbox": {"x": 50, "y": 50, "width": 500, "height": 100},
      "contains": ["elem_001", "elem_002"]
    },
    {
      "id": "block_002",
      "type": "diagram_area",
      "bbox": {"x": 50, "y": 160, "width": 400, "height": 300}
    }
  ],
  "diagram_candidates": [
    {
      "id": "diag_001",
      "diagram_type": "function_graph",
      "confidence": 0.85,
      "bbox": {"x": 60, "y": 170, "width": 380, "height": 280},
      "detected_elements": {
        "coordinate_system": {
          "type": "cartesian_2d",
          "x_axis": {"visible": true, "label": "x", "range_inferred": [-3, 5]},
          "y_axis": {"visible": true, "label": "y", "range_inferred": [-2, 10]}
        },
        "curves": [
          {
            "id": "curve_001",
            "type": "parabola",
            "inferred_equation": "y = x^2 + 2x + 1",
            "key_points": [
              {"type": "vertex", "coords": [-1, 0], "confidence": 0.9},
              {"type": "y_intercept", "coords": [0, 1], "confidence": 0.95}
            ],
            "asserted": false,
            "inferred": true
          }
        ],
        "labels": [
          {"text": "f(x)", "position": [2, 5], "confidence": 0.88}
        ]
      },
      "provenance": "claude_opus_4.5_vision",
      "uncertainty": 0.15,
      "review_required": false,
      "review_severity": null,
      "evidence_refs": ["img_001:bbox(60,170,380,280)"]
    }
  ]
}
```

**실패 모드:**
- 도형 유형 판별 불가 → `diagram_type: "unknown"`, `review_required: true`
- 좌표계 불명확 → `coordinate_system.type: "ambiguous"`

**가드레일:**
- 모든 좌표 추출에 `confidence` 점수 필수
- `asserted` vs `inferred` 명확 구분

---

### D. Alignment & Consistency Check (정합성 검증)

**목적:** Mathpix 텍스트와 Vision 파싱 결과 간 교차 검증

**입력:** text_spec + layout_blocks + diagram_candidates

**출력:**
```json
{
  "alignment_report": {
    "matched_pairs": [
      {
        "text_element": "elem_001",
        "diagram_element": "curve_001",
        "match_type": "equation_to_curve",
        "consistency_score": 0.92,
        "discrepancies": []
      }
    ],
    "unmatched_text": [],
    "unmatched_diagram": []
  },
  "inconsistencies": [
    {
      "id": "incon_001",
      "type": "coefficient_mismatch",
      "description": "텍스트의 'x^2 + 2x + 1'과 그래프 vertex 위치 불일치 가능성",
      "severity": "warning",
      "affected_elements": ["elem_001", "curve_001"],
      "suggested_quick_fix": {
        "action": "verify_vertex_position",
        "options": [
          {"label": "텍스트 기준 유지", "value": "keep_text"},
          {"label": "그래프 기준 수정", "value": "keep_graph"}
        ]
      },
      "review_required": true,
      "review_severity": "medium",
      "review_reason_code": "POTENTIAL_COEFFICIENT_MISMATCH",
      "downstream_risk": "재생성 시 잘못된 그래프 출력 가능"
    }
  ],
  "overall_consistency": "acceptable_with_warnings",
  "blocker_count": 0,
  "warning_count": 1
}
```

**실패 모드:**
- blocker_count > 0 → 파이프라인 중단, Human Review 강제 진입

**데이터 계약 (D→E):**
- `blocker_count == 0`일 때만 E 단계 진행
- 모든 `inconsistencies`는 G 단계로 전달

---

### E. Semantic Graph Build (의미 그래프 구축)

**목적:** 문제 요소 간 관계를 그래프 구조로 표현

**입력:** alignment_report + diagram_candidates

**v2.0.0 동적 Threshold 시스템:**

Stage E는 v2.0.0부터 3-layer 동적 threshold 아키텍처를 사용한다:

| Layer | 역할 | 예시 |
|-------|------|------|
| **Base Threshold** | Element type별 기본값 | `points: 0.65`, `curves: 0.70` |
| **Context Adjustment** | 환경 기반 조정 | `difficulty: hard → -0.05` |
| **Feedback Adaptation** | 사용자 피드백 반영 | `false_positive_rate > 0.3 → +0.03` |

```python
# GraphBuilderConfig에서 동적 threshold 사용
config = GraphBuilderConfig(
    threshold_config=ThresholdConfig(...),
    threshold_context=ThresholdContext(
        difficulty="medium",
        domain="algebra",
        image_quality="high"
    ),
    feedback_stats=FeedbackStats(
        total_reviews=100,
        false_positive_rate=0.15
    )
)

# Node/Edge 생성 시 element type별 threshold 자동 적용
effective_threshold = config.get_effective_node_threshold("point")  # 예: 0.63
```

**Threshold 적용 시점:**
- 그래프 빌드 후 `_apply_dynamic_thresholds()` 호출
- 각 node/edge의 `applied_threshold` 필드에 동적 계산된 값 저장
- `threshold_passed` 및 `review` 필드는 동적 threshold 기준으로 computed

**출력:**
```json
{
  "semantic_graph": {
    "schema_version": "2.0.0",
    "nodes": [
      {
        "id": "node_func_001",
        "type": "function",
        "label": "f",
        "properties": {
          "expression": "x^2 + 2x + 1",
          "domain": "all_real",
          "family": "quadratic"
        },
        "confidence": 0.85,
        "applied_threshold": 0.68,
        "threshold_passed": true,
        "review": {
          "review_required": false
        }
      },
      {
        "id": "node_point_001",
        "type": "point",
        "label": "vertex",
        "properties": {
          "coords": [-1, 0],
          "asserted": false,
          "inferred": true
        },
        "confidence": 0.72,
        "applied_threshold": 0.63,
        "threshold_passed": true,
        "review": {
          "review_required": false
        }
      },
      {
        "id": "node_axis_x",
        "type": "axis",
        "label": "x-axis",
        "properties": {"orientation": "horizontal"},
        "confidence": 0.55,
        "applied_threshold": 0.60,
        "threshold_passed": false,
        "review": {
          "review_required": true,
          "review_severity": "medium",
          "review_reason": "Confidence 0.55 below threshold 0.60"
        }
      }
    ],
    "edges": [
      {
        "id": "edge_001",
        "source": "node_func_001",
        "target": "node_point_001",
        "relation": "has_vertex",
        "confidence": 0.78,
        "applied_threshold": 0.55,
        "threshold_passed": true
      },
      {
        "id": "edge_002",
        "source": "node_func_001",
        "target": "node_axis_x",
        "relation": "intersects_at",
        "properties": {"intersection_points": [[-1, 0]]},
        "confidence": 0.62,
        "applied_threshold": 0.55,
        "threshold_passed": true
      }
    ],
    "constraints": [
      {
        "id": "constraint_001",
        "type": "symmetry",
        "axis": "x = -1",
        "affected_nodes": ["node_func_001"]
      }
    ],
    "threshold_config_version": "2.0.0",
    "ambiguity_set": [],
    "provenance": "pipeline_inference",
    "review_required": true,
    "review_severity": "medium",
    "review_reason": "1 nodes below threshold"
  }
}
```

---

### F. Regeneration Layer (재생성 사양)

**목적:** Desmos/GeoGebra API 호환 형식으로 변환

**입력:** semantic_graph

**출력:**
```json
{
  "regeneration_spec": {
    "format_version": "1.0",
    "target_platforms": ["desmos", "geogebra"],
    "desmos_state": {
      "expressions": [
        {
          "id": "expr_f",
          "latex": "f(x)=x^{2}+2x+1",
          "color": "#2d70b3",
          "lineStyle": "SOLID",
          "lineWidth": 2.5
        },
        {
          "id": "expr_vertex",
          "latex": "(-1, 0)",
          "color": "#c74440",
          "pointStyle": "POINT",
          "pointSize": 9,
          "label": "꼭짓점",
          "showLabel": true
        }
      ],
      "viewport": {
        "xmin": -5, "xmax": 3, "ymin": -2, "ymax": 8
      }
    },
    "geogebra_commands": [
      "f(x) = x^2 + 2*x + 1",
      "V = Vertex(f)",
      "SetColor(f, 45, 112, 179)",
      "SetCaption(V, \"꼭짓점\")",
      "SetLabelVisible(V, true)"
    ],
    "custom_json": {
      "problem_id": "prob_001",
      "elements": [
        {
          "id": "func_f",
          "type": "function",
          "expression": "x^2 + 2x + 1",
          "style": {"color": "#2d70b3", "stroke_width": 2},
          "modifiable_params": ["a", "b", "c"],
          "param_mapping": {"a": 1, "b": 2, "c": 1}
        }
      ]
    },
    "provenance": "semantic_graph_transform",
    "review_required": false,
    "suggested_quick_fix": null
  }
}
```

**Desmos 호환 참고사항:**
- LaTeX 문자열에서 백슬래시 이중 이스케이프 필요 (`\\sin`)
- State 형식은 opaque로 취급, expression 단위 조작만 권장

**GeoGebra 호환 참고사항:**
- 명령어는 영문으로 작성
- 복합 객체는 명령 순서에 의존

---

### G. Human-in-the-loop Review (사람 검토)

**목적:** `review_required: true` 항목에 대한 사람의 판단 및 수정

**입력:** 전체 파이프라인 산출물 중 `review_required: true` 항목

**v2.0.0 동적 Priority Scoring:**

Stage G의 PriorityScorer는 v2.0.0부터 동적 threshold 시스템을 사용하여 검토 우선순위를 결정한다:

| Priority Level | Threshold Scaling | 설명 |
|----------------|-------------------|------|
| **CRITICAL** | Base × 0.50 | 가장 낮은 threshold, 가장 높은 검토 긴급도 |
| **HIGH** | Base × 0.75 | 중상위 긴급도 |
| **MEDIUM** | Base × 1.00 | 기본 threshold 적용 |

```python
# PriorityScorerConfig에서 동적 threshold 사용
config = PriorityScorerConfig(
    threshold_config=ThresholdConfig(...),
    threshold_context=ThresholdContext(
        difficulty="medium",
        domain="algebra"
    ),
    feedback_stats=FeedbackStats(...)
)

scorer = PriorityScorer(config)

# Element type별 동적 threshold로 우선순위 결정
# 예: "equation" type의 base threshold가 0.70일 때
#   - CRITICAL threshold: 0.70 × 0.50 = 0.35
#   - HIGH threshold: 0.70 × 0.75 = 0.525
#   - MEDIUM threshold: 0.70 × 1.00 = 0.70
```

**Priority 계산 공식:**

| Factor | Weight | 설명 |
|--------|--------|------|
| Confidence Score | 0.35 | 동적 threshold 대비 confidence 갭 |
| Complexity Score | 0.25 | Element type별 복잡도 (equation: 0.8, label: 0.3) |
| Urgency Score | 0.20 | Due date 및 queue age 기반 |
| Business Score | 0.20 | Escalation, repeat assignment 등 |

**Explain Score 출력 예시:**
```json
{
  "task_id": "task_001",
  "scores": {
    "confidence": {"raw": 0.85, "weight": 0.35, "weighted": 0.2975},
    "complexity": {"raw": 0.70, "weight": 0.25, "weighted": 0.175},
    "urgency": {"raw": 0.50, "weight": 0.20, "weighted": 0.10},
    "business": {"raw": 0.20, "weight": 0.20, "weighted": 0.04}
  },
  "total_score": 0.6125,
  "priority": "high",
  "thresholds_applied": {
    "dynamic_enabled": true,
    "critical": 0.35,
    "high": 0.525,
    "medium": 0.70
  }
}
```

**출력:**
```json
{
  "correction_patch": {
    "patch_id": "patch_001",
    "timestamp": "2026-01-14T10:30:00Z",
    "reviewer": "user_001",
    "corrections": [
      {
        "target": "curve_001.key_points[0].coords",
        "original_value": [-1, 0],
        "corrected_value": [-1, 0],
        "action": "confirmed",
        "comment": "vertex 위치 정확함 확인"
      }
    ]
  },
  "approval_state": {
    "status": "approved",
    "blocker_resolved": true,
    "warnings_acknowledged": ["incon_001"],
    "ready_for_export": true
  }
}
```

---

### H. Export Spec (최종 출력)

**목적:** DOCX 생성 사양 또는 최종 JSON 산출

**입력:** correction_patch + regeneration_spec

**출력:**
```json
{
  "docx_generation_spec": {
    "template": "math_problem_standard",
    "sections": [
      {
        "type": "problem_text",
        "content": "다음 함수의 그래프를 그리시오.",
        "format": "paragraph"
      },
      {
        "type": "equation",
        "latex": "f(x) = x^2 + 2x + 1",
        "format": "display_math"
      },
      {
        "type": "embedded_graph",
        "source": "desmos_screenshot",
        "dimensions": {"width": 400, "height": 300}
      }
    ],
    "metadata": {
      "problem_id": "prob_001",
      "difficulty": "medium",
      "topic": ["quadratic_function", "graphing"]
    }
  }
}
```

---

## 4. JSON 스키마 제안

### Schema-Layout (문제 단위 분할 + 블록 + 상대 배치)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MathProblemLayout",
  "type": "object",
  "required": ["problem_id", "blocks", "review_required"],
  "properties": {
    "problem_id": {"type": "string"},
    "source_image": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "dimensions": {
          "type": "object",
          "properties": {
            "width": {"type": "integer"},
            "height": {"type": "integer"}
          }
        }
      }
    },
    "blocks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "bbox", "provenance", "review_required"],
        "properties": {
          "id": {"type": "string"},
          "type": {
            "type": "string",
            "enum": ["problem_statement", "equation", "diagram_area", "answer_space", "instruction"]
          },
          "bbox": {
            "type": "object",
            "properties": {
              "x": {"type": "number"},
              "y": {"type": "number"},
              "width": {"type": "number"},
              "height": {"type": "number"}
            }
          },
          "relative_position": {
            "type": "object",
            "properties": {
              "above": {"type": "string"},
              "below": {"type": "string"},
              "left_of": {"type": "string"},
              "right_of": {"type": "string"}
            }
          },
          "contains": {
            "type": "array",
            "items": {"type": "string"}
          },
          "provenance": {"type": "string"},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1},
          "uncertainty": {"type": "number", "minimum": 0, "maximum": 1},
          "review_required": {"type": "boolean"},
          "review_severity": {
            "type": "string",
            "enum": ["blocker", "high", "medium", "low", null]
          },
          "review_reason_code": {"type": "string"},
          "evidence_refs": {
            "type": "array",
            "items": {"type": "string"}
          },
          "suggested_quick_fix": {
            "type": "object",
            "properties": {
              "action": {"type": "string"},
              "options": {"type": "array"}
            }
          }
        }
      }
    },
    "review_required": {"type": "boolean"},
    "downstream_risk": {"type": "string"}
  }
}
```

### Schema-Diagram (좌표계/도형/그래프/라벨)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MathDiagram",
  "type": "object",
  "required": ["diagram_id", "diagram_type", "elements", "review_required"],
  "properties": {
    "diagram_id": {"type": "string"},
    "diagram_type": {
      "type": "string",
      "enum": ["function_graph", "geometric_figure", "statistical_chart", "coordinate_plane", "number_line", "venn_diagram", "unknown"]
    },
    "coordinate_system": {
      "type": "object",
      "properties": {
        "type": {"type": "string", "enum": ["cartesian_2d", "cartesian_3d", "polar", "none", "ambiguous"]},
        "x_axis": {
          "type": "object",
          "properties": {
            "visible": {"type": "boolean"},
            "label": {"type": "string"},
            "range_asserted": {"type": "array", "items": {"type": "number"}},
            "range_inferred": {"type": "array", "items": {"type": "number"}},
            "tick_interval": {"type": "number"}
          }
        },
        "y_axis": {"$ref": "#/properties/coordinate_system/properties/x_axis"},
        "origin": {
          "type": "object",
          "properties": {
            "coords": {"type": "array", "items": {"type": "number"}},
            "visible": {"type": "boolean"}
          }
        }
      }
    },
    "elements": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "element_type", "asserted", "inferred", "provenance", "review_required"],
        "properties": {
          "id": {"type": "string"},
          "element_type": {
            "type": "string",
            "enum": ["point", "line", "segment", "ray", "circle", "ellipse", "polygon", "curve", "function", "label", "shading", "arrow", "angle_mark"]
          },
          "geometry": {
            "type": "object",
            "properties": {
              "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
              "center": {"type": "array", "items": {"type": "number"}},
              "radius": {"type": "number"},
              "vertices": {"type": "array"},
              "equation": {"type": "string"},
              "parametric": {"type": "object"}
            }
          },
          "style": {
            "type": "object",
            "properties": {
              "stroke_color": {"type": "string"},
              "fill_color": {"type": "string"},
              "stroke_width": {"type": "number"},
              "stroke_style": {"type": "string", "enum": ["solid", "dashed", "dotted"]},
              "fill_opacity": {"type": "number"}
            }
          },
          "label": {
            "type": "object",
            "properties": {
              "text": {"type": "string"},
              "position": {"type": "array", "items": {"type": "number"}},
              "orientation": {"type": "string"}
            }
          },
          "asserted": {"type": "boolean"},
          "inferred": {"type": "boolean"},
          "confidence": {"type": "number"},
          "provenance": {"type": "string"},
          "uncertainty": {"type": "number"},
          "review_required": {"type": "boolean"},
          "review_severity": {"type": "string"},
          "review_reason_code": {"type": "string"},
          "evidence_refs": {"type": "array", "items": {"type": "string"}},
          "suggested_quick_fix": {"type": "object"},
          "downstream_risk": {"type": "string"}
        }
      }
    },
    "relationships": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "type": {
            "type": "string",
            "enum": ["perpendicular", "parallel", "tangent", "intersects", "congruent", "similar", "bisects", "passes_through"]
          },
          "participants": {"type": "array", "items": {"type": "string"}},
          "asserted": {"type": "boolean"},
          "inferred": {"type": "boolean"},
          "confidence": {"type": "number"}
        }
      }
    },
    "constraints": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "constraint_type": {"type": "string"},
          "parameters": {"type": "object"},
          "affected_elements": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "ambiguity_set": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "element_id": {"type": "string"},
          "possible_interpretations": {"type": "array"},
          "recommended": {"type": "string"}
        }
      }
    },
    "review_required": {"type": "boolean"},
    "review_severity": {"type": "string"},
    "review_reason_code": {"type": "string"}
  }
}
```

### 실제 채워진 JSON 예시 (이차함수 그래프 문제)

```json
{
  "problem_id": "prob_quadratic_001",
  "source_image": {
    "id": "img_001",
    "dimensions": {"width": 1200, "height": 800}
  },
  "blocks": [
    {
      "id": "block_statement",
      "type": "problem_statement",
      "bbox": {"x": 50, "y": 30, "width": 600, "height": 80},
      "relative_position": {"above": "block_diagram"},
      "contains": ["elem_instruction", "elem_equation"],
      "provenance": "claude_opus_4.5_vision",
      "confidence": 0.95,
      "uncertainty": 0.05,
      "review_required": false,
      "review_severity": null,
      "review_reason_code": null,
      "evidence_refs": ["img_001:bbox(50,30,600,80)"],
      "suggested_quick_fix": null
    },
    {
      "id": "block_diagram",
      "type": "diagram_area",
      "bbox": {"x": 100, "y": 150, "width": 450, "height": 400},
      "relative_position": {"below": "block_statement"},
      "contains": ["diag_001"],
      "provenance": "claude_opus_4.5_vision",
      "confidence": 0.88,
      "uncertainty": 0.12,
      "review_required": false,
      "review_severity": null,
      "review_reason_code": null,
      "evidence_refs": ["img_001:bbox(100,150,450,400)"],
      "suggested_quick_fix": null
    }
  ],
  "diagram": {
    "diagram_id": "diag_001",
    "diagram_type": "function_graph",
    "coordinate_system": {
      "type": "cartesian_2d",
      "x_axis": {
        "visible": true,
        "label": "x",
        "range_asserted": null,
        "range_inferred": [-4, 4],
        "tick_interval": 1
      },
      "y_axis": {
        "visible": true,
        "label": "y",
        "range_asserted": null,
        "range_inferred": [-2, 10],
        "tick_interval": 1
      },
      "origin": {
        "coords": [0, 0],
        "visible": true
      }
    },
    "elements": [
      {
        "id": "elem_parabola",
        "element_type": "function",
        "geometry": {
          "equation": "y = x^2 + 2x + 1",
          "parametric": {
            "form": "standard",
            "a": 1, "b": 2, "c": 1
          }
        },
        "style": {
          "stroke_color": "#2d70b3",
          "stroke_width": 2,
          "stroke_style": "solid"
        },
        "label": {
          "text": "f(x)",
          "position": [1.5, 6],
          "orientation": "right"
        },
        "asserted": false,
        "inferred": true,
        "confidence": 0.89,
        "provenance": "claude_opus_4.5_vision + mathpix_alignment",
        "uncertainty": 0.11,
        "review_required": false,
        "review_severity": null,
        "review_reason_code": null,
        "evidence_refs": ["elem_equation:latex", "img_001:curve_trace"],
        "suggested_quick_fix": null,
        "downstream_risk": null
      },
      {
        "id": "elem_vertex",
        "element_type": "point",
        "geometry": {
          "points": [[-1, 0]]
        },
        "style": {
          "stroke_color": "#c74440",
          "fill_color": "#c74440"
        },
        "label": {
          "text": "꼭짓점(-1, 0)",
          "position": [-1.5, -0.5],
          "orientation": "below"
        },
        "asserted": false,
        "inferred": true,
        "confidence": 0.92,
        "provenance": "claude_opus_4.5_vision",
        "uncertainty": 0.08,
        "review_required": false,
        "review_severity": null,
        "review_reason_code": null,
        "evidence_refs": ["img_001:point_detection(-1,0)"],
        "suggested_quick_fix": null,
        "downstream_risk": null
      },
      {
        "id": "elem_y_intercept",
        "element_type": "point",
        "geometry": {
          "points": [[0, 1]]
        },
        "style": {
          "stroke_color": "#388c46",
          "fill_color": "#388c46"
        },
        "label": {
          "text": "(0, 1)",
          "position": [0.3, 1.2],
          "orientation": "right"
        },
        "asserted": false,
        "inferred": true,
        "confidence": 0.94,
        "provenance": "claude_opus_4.5_vision",
        "uncertainty": 0.06,
        "review_required": false,
        "review_severity": null,
        "review_reason_code": null,
        "evidence_refs": ["img_001:point_detection(0,1)"],
        "suggested_quick_fix": null,
        "downstream_risk": null
      }
    ],
    "relationships": [
      {
        "id": "rel_vertex_on_curve",
        "type": "passes_through",
        "participants": ["elem_parabola", "elem_vertex"],
        "asserted": false,
        "inferred": true,
        "confidence": 0.95
      }
    ],
    "constraints": [
      {
        "id": "const_symmetry",
        "constraint_type": "axis_of_symmetry",
        "parameters": {"axis": "x = -1"},
        "affected_elements": ["elem_parabola"]
      }
    ],
    "ambiguity_set": [],
    "review_required": false,
    "review_severity": null,
    "review_reason_code": null
  },
  "review_required": false,
  "downstream_risk": null
}
```

---

## 5. Human-in-the-loop 설계

### Review Queue 설계

`review_severity` 기반 자동 정렬 규칙:

| 우선순위 | review_severity | 설명 | 처리 방식 |
|---------|-----------------|------|----------|
| 1 | `blocker` | 파이프라인 진행 불가 | 즉시 처리 필수 |
| 2 | `high` | 재생성 결과에 중대한 영향 | 당일 내 처리 권장 |
| 3 | `medium` | 부분적 불확실성 존재 | 배치 처리 가능 |
| 4 | `low` | 미미한 불확실성 | 선택적 처리 |

Queue 인터페이스 요구사항:
- `review_severity` 기준 자동 정렬
- 동일 severity 내에서는 `confidence` 오름차순 (낮은 것 먼저)
- 필터링: severity, problem_type, date_range

### Evidence Overlay 설계

검토자에게 제공되는 시각적 오버레이:

```
┌─────────────────────────────────────────┐
│  [원본 이미지]                            │
│                                          │
│    ┌─────────────────┐                   │
│    │ bbox: elem_001  │ ← 파란색 실선      │
│    │ (방정식 텍스트)   │                   │
│    └─────────────────┘                   │
│                                          │
│    ┌───────────────────────┐             │
│    │ bbox: diag_001        │ ← 녹색 점선  │
│    │ (도형 영역)             │             │
│    │   ● vertex (빨간 점)   │             │
│    │   ─ curve (파란 선)    │             │
│    └───────────────────────┘             │
│                                          │
│  [Evidence Panel]                        │
│  • elem_001: "y = x² + 2x + 1" (conf: 0.92)│
│  • curve_001: inferred from text + visual │
│  • vertex: detected at (-1, 0) (conf: 0.90)│
└─────────────────────────────────────────┘
```

오버레이 색상 규칙:
- **파란색 실선**: Mathpix에서 추출된 텍스트 요소
- **녹색 점선**: Claude Vision에서 파싱된 도형 영역
- **빨간색 강조**: `review_required: true` 항목
- **노란색 배경**: `ambiguity_set`에 포함된 요소

### One-click Fix 템플릿

`suggested_quick_fix` 기반 빠른 수정 UI:

```json
{
  "suggested_quick_fix": {
    "action": "select_interpretation",
    "prompt": "꼭짓점 좌표를 확인해주세요",
    "options": [
      {
        "label": "(-1, 0) 유지",
        "value": {"coords": [-1, 0]},
        "confidence_boost": 0.1
      },
      {
        "label": "(-1, 1)로 수정",
        "value": {"coords": [-1, 1]},
        "confidence_boost": 0
      },
      {
        "label": "직접 입력",
        "value": "custom",
        "input_type": "coordinate_pair"
      }
    ],
    "auto_apply": false
  }
}
```

Quick Fix 유형:
- `select_interpretation`: 다중 해석 중 선택
- `confirm_value`: 값 확인/승인
- `edit_value`: 직접 수정 입력
- `delete_element`: 잘못된 요소 삭제
- `add_element`: 누락된 요소 추가

### Consistency Gate 규칙

Blocker를 0으로 만드는 필수 조건:

```
CONSISTENCY_GATE_RULES:
  1. ALL elements WHERE review_severity == "blocker" 
     MUST have approval_state.status == "resolved"
  
  2. text_spec.extracted_elements[] 와 diagram_candidates[] 간
     unmatched 항목이 있으면 review_severity = "high" 이상으로 처리
  
  3. coordinate_system.type == "ambiguous" 인 경우
     반드시 사람이 유형 확정 필요
  
  4. ambiguity_set.length > 0 인 경우
     각 항목에 대해 recommended 값 확정 필요
  
  5. confidence < 0.5 인 모든 요소는
     review_severity = "high" 자동 할당
```

게이트 통과 조건:
- `blocker_count == 0`
- `high_severity_unresolved == 0`
- `ambiguity_set` 내 모든 항목 resolved

### Correction Patch 기록

```json
{
  "correction_patch": {
    "patch_id": "patch_20260114_001",
    "timestamp": "2026-01-14T14:30:00+09:00",
    "reviewer_id": "reviewer_kim",
    "session_duration_seconds": 120,
    "corrections": [
      {
        "correction_id": "corr_001",
        "target_path": "diagram.elements[0].geometry.equation",
        "original_value": "y = x^2 + 2x + 1",
        "corrected_value": "y = x^2 + 2x + 1",
        "action": "confirmed",
        "reason": "텍스트와 그래프 일치 확인",
        "timestamp": "2026-01-14T14:31:15+09:00"
      },
      {
        "correction_id": "corr_002",
        "target_path": "diagram.elements[1].geometry.points[0]",
        "original_value": [-1, 0],
        "corrected_value": [-1, 0],
        "action": "confirmed",
        "reason": "꼭짓점 위치 정확",
        "timestamp": "2026-01-14T14:31:45+09:00"
      }
    ],
    "new_elements_added": [],
    "elements_deleted": [],
    "approval_state": {
      "status": "approved",
      "blocker_resolved": true,
      "warnings_acknowledged": [],
      "final_confidence": 0.95
    }
  }
}
```

---

## 6. 한계와 대안

### Claude Native Vision 가능/어려운 범위

**가능한 영역 (높은 신뢰도):**
- 기본 좌표계 인식 (직교 좌표, 원점, 축)
- 단순 도형 검출 (점, 직선, 원, 삼각형, 사각형)
- 함수 그래프 유형 분류 (직선, 포물선, 삼각함수 등)
- 레이블 텍스트 위치 파악
- 문제 영역과 도형 영역 구분

**어려운 영역 (낮은 신뢰도, review_required 필수):**
- **정밀 좌표 추출**: 픽셀 단위 정확도 요구 시 불확실성 높음
- **복잡한 공간 관계**: 여러 도형 간 미세한 위치 관계 (접선, 수직이등분선 등)
- **3D 도형**: 입체도형의 깊이 정보 추론 한계
- **손글씨 도형**: 정형화되지 않은 스케치 해석
- **밀집 레이블**: 작고 빽빽한 텍스트 구분

### 추가 기술 스택 옵션

**Vectorization (이미지 → 벡터 변환)**

| 도구 | 특징 | 활용 |
|------|------|------|
| **StarVector** | AI 기반 semantic-aware SVG 생성, CVPR 2025 | 기술 도형/그래프에 최적 |
| **VTracer** | 컬러 이미지 지원, O(n) 알고리즘 | 다색 다이어그램 처리 |
| **Potrace** | 모노크롬 전용, 안정적 | 흑백 선화 벡터화 |

StarVector GitHub: https://github.com/joanrod/star-vector
VTracer GitHub: https://github.com/visioncortex/vtracer

**Graph Digitization (그래프 → 데이터 추출)**

| 도구 | 특징 | 활용 |
|------|------|------|
| **WebPlotDigitizer** | 업계 표준, semi-automatic | 수동 검증 포함 추출 |
| **ChartOCR/LineEX** | Deep learning 기반 자동화 | 배치 처리 |
| **Energent.ai** | AI 기반 batch 처리 | 대량 데이터 추출 |

WebPlotDigitizer: https://automeris.io/
ChartOCR 논문: WACV 2021

**Constraint Solving (기하 제약 해석)**

| 도구 | 특징 | 활용 |
|------|------|------|
| **SolveSpace** | 오픈소스, Newton's method | 파이프라인 통합 가능 |
| **GeoSolver** | Python 네이티브 | ML 파이프라인 연동 |
| **D-Cubed DCM** | 상용, 업계 표준 | 엔터프라이즈 환경 |

SolveSpace: https://solvespace.com/tech.pl

**Symbolic Math (CAS)**

| 도구 | 특징 | 활용 |
|------|------|------|
| **SymPy** | Python, geometry module 포함 | 수식 검증, 좌표 계산 |
| **SageMath** | 종합 수학 시스템 | 복잡한 연산 필요 시 |
| **SymEngine** | C++ 고성능 | 대규모 처리 시 |

SymPy 문서: https://docs.sympy.org/

**Diagram Parsing Research**

| 리소스 | 특징 |
|--------|------|
| **AI2D Dataset** | 4,903개 도형 + annotation, 학습 데이터 |
| **ChartEye** | 차트 정보 추출 프레임워크 |
| **mPLUG-PaperOwl** | 과학 도형 MLLM |

AI2D: https://prior.allenai.org/projects/diagram-understanding

### "함수 형태 변경 + 도형 관계 재생성" 난이도 분석

**핵심 과제:** 단순 계수 변경을 넘어 함수 형태 자체를 변형하고, 도형 간 관계(평행, 수직, 접선 등)를 유지하면서 재생성

**(A) 최소 목표: 계수/파라미터 변경**

현재 파이프라인으로 **달성 가능**:
- `param_mapping`을 통해 a, b, c 계수 분리 저장
- Desmos `setExpression()` 또는 GeoGebra `setValue()`로 동적 변경
- Slider를 통한 인터랙티브 조작

```json
{
  "modifiable_params": ["a", "b", "c"],
  "param_mapping": {"a": 1, "b": 2, "c": 1},
  "regeneration_template": "y = {a}x^2 + {b}x + {c}"
}
```

**(B) 상위 목표: 함수 형태 변경 + 관계 재생성**

**난이도가 높은 이유:**
1. 함수 형태 변경(예: 이차→삼차)은 근본적으로 다른 기하적 특성 요구
2. 도형 관계(접선, 수직)는 제약 조건 시스템 필요
3. 원본 문제의 "의도"를 이해해야 유의미한 변형 가능

**달성을 위한 외부 솔루션:**

| 접근법 | 설명 | 구현 복잡도 |
|--------|------|-----------|
| **Constraint Solver 통합** | SolveSpace/GeoSolver로 관계 유지 | 중-상 |
| **Parametric Template** | 미리 정의된 변형 패턴 라이브러리 | 중 |
| **GeoGebra Construction Protocol** | 구성 순서 기록 후 재실행 | 중 |
| **Symbolic Verification** | SymPy로 관계 보존 검증 | 중 |

**권장 전략:**
1. Semantic Graph의 `constraints` 배열에 관계 명시적 저장
2. 재생성 시 GeoGebra command sequence 활용 (관계 유지 명령 포함)
3. 변형 후 SymPy로 관계 보존 여부 검증
4. 검증 실패 시 `review_required: true` 트리거

**예시: 접선 관계 유지 재생성**
```javascript
// GeoGebra 명령 시퀀스
"f(x) = x^2"           // 원본 포물선
"g = Tangent(f, A)"    // A에서 접선 (관계 정의)
"SetValue(f, x^3)"     // 함수 형태 변경
// → g는 자동으로 새 함수의 A점 접선으로 업데이트
```

이 접근법은 GeoGebra의 동적 기하 특성을 활용하여 관계를 **선언적으로** 정의함으로써, 함수 형태 변경 시에도 관계가 자동 유지되도록 한다.

---

## 결론

이 파이프라인은 **Human-in-the-loop를 핵심 설계 원칙**으로 삼아, Claude Opus 4.5의 Native Vision 기능과 Claude Code v2.1.7의 최신 기능을 최대한 활용한다. 모든 파싱 산출물에 `provenance`, `uncertainty`, `review_required`, `suggested_quick_fix`를 필수 포함함으로써, 불확실성이 높은 결과에 대해 사람의 판단을 보장한다.

**핵심 설계 원칙:**
- `review_required` 플래그 체계를 통한 Human 검토 게이트
- `asserted` vs `inferred` 구분으로 출처 명확화
- `ambiguity_set`을 통한 다중 해석 가능성 표현
- Desmos/GeoGebra 이중 지원으로 재생성 유연성 확보

**v2.0.0 신규 기능:**
- **3-layer 동적 threshold 시스템**: Base → Context → Feedback 아키텍처
- **Element type별 적응형 threshold**: `points`, `curves`, `equations` 등 27개 타입 지원
- **Stage E/G 통합**: SemanticGraph와 HumanReview에서 동적 threshold 적용
- **Feedback-driven adaptation**: 사용자 피드백 기반 threshold 자동 조정

**향후 확장 방향:**
- Constraint Solver 통합으로 관계 유지 재생성 강화
- StarVector 등 AI 기반 vectorization 통합
- 3D 도형 지원을 위한 GeoGebra 3D API 연동
- Threshold calibration 자동화를 위한 ML pipeline 통합

이 Blueprint는 수학 문제 이미지를 "재사용/변형 가능한 구조화 데이터"로 변환하는 현실적인 경로를 제시하며, 각 단계에서 발생할 수 있는 불확실성을 체계적으로 관리할 수 있는 프레임워크를 제공한다.