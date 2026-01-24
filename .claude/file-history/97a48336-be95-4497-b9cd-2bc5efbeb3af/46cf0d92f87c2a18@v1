# Template 3: 테스트 프레임워크 설계

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | HIGH |
| Total Tasks | 4 |
| Golden Dataset Size | 250+ samples |
| Stage Metrics | 8 (A-H) |

## Problem Statement

**현재 설계의 Gap:**
1. 테스트 전략 부재 - 파이프라인 품질 검증 방법 없음
2. Golden Dataset 미정의 - 정답 데이터 없이 정확도 측정 불가
3. CI/CD 통합 계획 없음 - 회귀 방지 메커니즘 부재
4. Stage별 평가 지표 미정의 - 각 단계 품질 기준 불명확

## Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Design | Golden Dataset 구조 및 어노테이션 스키마 설계 | COMPLETED |
| 2 | Design | Stage별 평가 지표 (Pydantic 스키마) 정의 | COMPLETED |
| 3 | Design | CI/CD 파이프라인 통합 전략 수립 | COMPLETED |
| 4 | Design | 회귀 테스트 및 Canary/A/B 테스트 전략 | COMPLETED |

## Key Findings

### 1. Golden Dataset Structure

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

### 2. Stage별 평가 지표 (요약)

| Stage | 주요 지표 | 통과 임계값 |
|-------|----------|------------|
| A. Ingestion | quality_score, blur_score | quality ≥ 0.6 |
| B. TextParse | CER, latex_structural_match | CER < 0.05, struct ≥ 0.9 |
| C. VisionParse | bbox_iou, label_recall | IoU ≥ 0.7, recall ≥ 0.85 |
| D. Alignment | alignment_f1, blocker_accuracy | F1 ≥ 0.85, blocker ≥ 0.95 |
| E. SemanticGraph | node_accuracy, edge_accuracy | node ≥ 0.9, edge ≥ 0.85 |
| F. Regeneration | param_accuracy, export_valid | param ≥ 0.95 |
| G. HumanReview | false_positive_rate | FP rate < 0.1 |
| H. Export | completeness_score | ≥ 0.95 |

### 3. CI/CD 파이프라인 계층

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

### 4. 변경 영향 분석 매핑

| 파일 변경 | 영향 Stage | 다운스트림 |
|----------|-----------|-----------|
| ingestion.py | A | B, C, D, E, F, G, H |
| mathpix_client.py | B | C, D, E, F, G, H |
| vision_parse.py | C | D, E, F, G, H |
| alignment.py | D | E, F, G, H |
| semantic_graph.py | E | F, G, H |
| regeneration.py | F | G, H |

## Golden Dataset Annotation Schema (핵심)

```python
class GoldenSampleAnnotation(BaseModel):
    sample_id: str
    source_image_path: str
    category: str  # e.g., "high_school/functions_advanced"

    # Stage B Ground Truth
    expected_equations: List[EquationAnnotation]

    # Stage C Ground Truth
    expected_diagrams: List[DiagramAnnotation]
    expected_labels: List[LabelAnnotation]

    # Stage D Ground Truth
    expected_text_vision_mapping: Dict[str, str]
    known_ambiguities: List[Dict[str, Any]]

    # Expected Review
    expected_review_required: bool
    expected_review_severity: Optional[str]
```

## Quality Gate Configuration

```yaml
# .github/quality-gates.yaml
pipeline_quality_gates:
  smoke_tests:
    blocking: true
    thresholds:
      pass_rate: 1.0

  regression_tests:
    blocking: true
    thresholds:
      overall_pass_rate: 0.90
      critical_stage_d_pass_rate: 0.95

  edge_case_coverage:
    blocking: true
    thresholds:
      handwritten_pass_rate: 0.70
      ambiguous_detection_rate: 0.90
```

## Implementation Phases

| Phase | 범위 | 기간 |
|-------|------|------|
| Phase 1 | Pydantic 스키마 + 50 샘플 + Smoke 테스트 | 2주 |
| Phase 2 | 전체 메트릭 + 150 샘플 + CI 워크플로우 | 2주 |
| Phase 3 | Canary/A/B + 250 샘플 완성 | 2주 |
| Phase 4 | 성능 벤치마크 + 문서화 | 2주 |

## Quick Resume After Auto-Compact

If context is compacted, resume by:
1. Read this file: `.agent/plans/template_3_test_framework_design.md`
2. Key decisions already made:
   - Golden Dataset: 250+ samples, 4 categories
   - Stage metrics: 8 Pydantic schemas
   - CI hierarchy: Smoke → Regression → Canary
   - A/B testing for model updates
3. Next: Template 4 Confidence Threshold Calibration

## Agent Registry

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Test Framework Design | adedc2a | completed | No |

## Sources

- Existing test patterns: `tests/conftest.py`, `tests/e2e/test_full_integration.py`
- Pipeline schemas: `lib/oda/ontology/objects/pipeline.py`
- Quality check patterns: `lib/oda/ontology/evidence/quality_checks.py`
