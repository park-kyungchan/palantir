# Template 4: Confidence Threshold Calibration

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | HIGH |
| Total Tasks | 3 |
| Element Types | 11 (across Stages B-E) |
| Threshold Range | 0.40 - 0.80 |

## Problem Statement

**현재 설계의 Gap:**
1. 고정 threshold (0.5) 사용 - 요소 타입별 리스크 차이 미반영
2. Precision-Recall 트레이드오프 분석 부재
3. 동적 조정 메커니즘 없음 - 시간에 따른 성능 변화 대응 불가
4. Human review 부담 최적화 전략 미정의

## Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Research | 요소 타입별 threshold 연구 | COMPLETED |
| 2 | Analysis | Precision-Recall 트레이드오프 분석 | COMPLETED |
| 3 | Design | 동적 threshold 조정 알고리즘 설계 | COMPLETED |

## Key Findings

### 1. Risk-Weighted Base Thresholds

| Element Type | Stage | Risk Level | Base Threshold | Default Severity |
|--------------|-------|------------|----------------|------------------|
| `equation` | B | CRITICAL | 0.70 | blocker |
| `text` | B | MEDIUM | 0.45 | medium |
| `diagram_type` | C | HIGH | 0.60 | high |
| `bbox` | C | LOW | 0.40 | low |
| `labels` | C | MEDIUM-HIGH | 0.55 | medium |
| `curves` | C | CRITICAL | 0.75 | blocker |
| `points` | C | HIGH | 0.65 | high |
| `alignment_match` | D | HIGH | 0.60 | high |
| `inconsistency` | D | CRITICAL | 0.80 | blocker |
| `node` | E | HIGH | 0.60 | high |
| `edge` | E | MEDIUM | 0.55 | medium |

### 2. Operating Point Targets

| Risk Level | Recall Target | Precision Target | Rationale |
|------------|---------------|------------------|-----------|
| CRITICAL | ≥ 0.98 | ≥ 0.60 | 오류 놓치지 않기 최우선 |
| HIGH | ≥ 0.95 | ≥ 0.70 | 균형 |
| MEDIUM | ≥ 0.90 | ≥ 0.75 | UX 영향 최소화 |
| LOW | ≥ 0.85 | ≥ 0.80 | 리뷰 효율성 |

### 3. 3-Layer Dynamic Adjustment Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3: FEEDBACK LOOP (Rolling window 100)            │
│  - FN rate > 0.05 → threshold 낮춤                      │
│  - FP rate > 0.30 → threshold 높임                      │
│  - Learning rate: 0.08                                  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│  Layer 2: CONTEXT MODIFIERS                             │
│  - image_quality: 0.85 + (quality_score * 0.15)        │
│  - complexity: elem=1.05, mid=1.0, high=0.95, adv=0.90 │
│  - density: 1.0 - (element_count * 0.01)               │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│  Layer 1: BASE THRESHOLDS (Quarterly calibration)       │
└─────────────────────────────────────────────────────────┘
```

### 4. Core Algorithm

```python
def compute_effective_threshold(element_type, context, feedback_stats):
    base = BASE_THRESHOLDS[element_type]

    # Context modifiers
    quality_mod = 0.85 + (context.image_quality_score * 0.15)
    complexity_mod = COMPLEXITY_MODS[context.problem_level]
    density_mod = 1.0 - (min(context.element_count, 10) * 0.01)
    context_modifier = quality_mod * complexity_mod * density_mod

    # Feedback loop
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

### 5. Hard Rules (Override Thresholds)

| Condition | Action | Severity |
|-----------|--------|----------|
| `confidence < 0.2` | ALWAYS review | blocker |
| `diagram_type == "unknown"` | ALWAYS review | high |
| `coordinate_system == "ambiguous"` | ALWAYS review | high |
| `blocker_count > 0` | Pipeline halt | - |

### 6. Monitoring & Alerts

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| False Negative Rate | < 0.05 | > 0.07 | > 0.10 |
| False Positive Rate | < 0.30 | > 0.40 | > 0.50 |
| Review Queue Depth | < 200 | > 300 | > 500 |
| Confidence Drift (KL) | < 0.10 | > 0.15 | > 0.25 |

## Configuration Schema (Summary)

```yaml
# config/threshold_calibration.yaml
global_settings:
  min_threshold: 0.15
  max_threshold: 0.90
  learning_rate: 0.08
  feedback_window_size: 100

targets:
  false_negative_rate: 0.05
  false_positive_rate: 0.30

element_thresholds:
  equation: {base: 0.70, risk: critical}
  curves: {base: 0.75, risk: critical}
  inconsistency: {base: 0.80, risk: critical}
  points: {base: 0.65, risk: high}
  diagram_type: {base: 0.60, risk: high}
  alignment_match: {base: 0.60, risk: high}
  node: {base: 0.60, risk: high}
  labels: {base: 0.55, risk: medium_high}
  edge: {base: 0.55, risk: medium}
  text: {base: 0.45, risk: medium}
  bbox: {base: 0.40, risk: low}
```

## Calibration Procedure

| Phase | 활동 | 주기 |
|-------|------|------|
| Initial | Golden Dataset으로 threshold sweep | 최초 1회 |
| Weekly | 리뷰어 피드백으로 precision/recall 계산 | 주간 |
| Monthly | 5% 이상 drift 시 재보정 | 월간 |
| Quarterly | 전체 재보정 + operating point 검토 | 분기 |

## Integration Points

```
mathpix.md 수정 위치:
├── Stage B (lines 149-196): equation/text threshold 적용
├── Stage C (lines 203-262): diagram/curves/points threshold 적용
├── Stage D (lines 275-328): alignment/inconsistency threshold 적용
└── Stage E (lines 332-398): node/edge threshold 적용
```

## Quick Resume After Auto-Compact

If context is compacted, resume by:
1. Read this file: `.agent/plans/template_4_confidence_threshold_calibration.md`
2. Key decisions already made:
   - Risk-weighted thresholds: 0.40 (bbox) to 0.80 (inconsistency)
   - 3-layer dynamic adjustment architecture
   - Operating targets: Recall ≥ 0.95 for critical elements
3. Next: Phase 5 통합 실행 계획

## Agent Registry

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Threshold Calibration Design | a924480 | completed | No |

## Sources

- Template 1: Hybrid confidence schema (combined_confidence)
- Template 2: detection_map Stage C trigger logic
- Template 3: Golden Dataset for calibration (250+ samples)
- mathpix.md: Existing review_required patterns
