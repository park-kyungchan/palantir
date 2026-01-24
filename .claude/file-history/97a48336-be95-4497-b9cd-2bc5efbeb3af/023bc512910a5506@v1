# MASTER CONTEXT REFERENCE

> **Purpose:** Auto-Compact 후 전체 컨텍스트 복구를 위한 마스터 참조 문서
> **Last Updated:** 2026-01-17
> **Project Status:** 설계 완료 (96%), 코드 구현 대기

---

## 🎯 Quick Resume After Auto-Compact

Auto-Compact 후 이 파일을 읽으면 전체 프로젝트 컨텍스트를 복구할 수 있습니다:

```
1. 이 파일 읽기: .agent/plans/MASTER_CONTEXT_REFERENCE.md
2. TodoWrite 상태 확인 (자동 복구됨)
3. 첫 번째 'pending' 태스크부터 진행
4. 상세 설계는 해당 Template 파일 참조
```

---

## 📋 Project Overview

| Item | Value |
|------|-------|
| **프로젝트명** | Math Image Parsing Pipeline v2.0 |
| **목표** | 수학 문제 이미지 → Desmos/GeoGebra 호환 데이터 변환 |
| **핵심 문서** | `/home/palantir/cow/docs/mathpix.md` |
| **설계 완성도** | 96% (목표 95%+ 달성) |
| **현재 단계** | 코드 구현 대기 |

---

## 🏗️ Architecture Summary

### 8-Stage Pipeline
```
A.Ingestion → B.TextParse → C.VisionParse → D.Alignment
                                                ↓
H.Export ← G.HumanReview ← F.Regeneration ← E.SemanticGraph
```

### Critical Design Decisions (From Templates)

| Decision | Template | Summary |
|----------|----------|---------|
| **Stage C: YOLO + Claude Hybrid** | T1 | Claude Vision은 bbox 불가 → YOLO 감지 + Claude 해석 |
| **Stage B: Mathpix API v3 Full** | T2 | detection_map, content_flags, line_segments 전체 활용 |
| **Test: Golden Dataset + CI/CD** | T3 | 250+ 샘플, Smoke→Regression→Canary 계층 |
| **Threshold: 3-Layer Dynamic** | T4 | Base → Context → Feedback 동적 조정 |

---

## 📁 Plan Files Index

| File | Purpose | Key Content |
|------|---------|-------------|
| `template_1_claude_vision_alternative.md` | Stage C 재설계 | YOLO26 + Claude Hybrid 아키텍처 |
| `template_2_mathpix_api_integration.md` | Stage B 강화 | detection_map → Stage C 트리거 |
| `template_3_test_framework_design.md` | 테스트 전략 | Golden Dataset 구조, CI/CD |
| `template_4_confidence_threshold_calibration.md` | Threshold 시스템 | 11개 요소별 위험 기반 threshold |
| `integration_execution_plan.md` | 마스터 실행 계획 | 6주 타임라인, 의존성 그래프 |
| `mathpix_v2_modifications.md` | 수정안 통합 | v2.0.0 스키마 전체 정의 |
| `design_completeness_verification.md` | 완성도 검증 | Stage별 점수, 96% 달성 확인 |
| `MASTER_CONTEXT_REFERENCE.md` | **이 파일** | 전체 컨텍스트 요약 |

---

## 🔢 Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] threshold_calibration.yaml 설정 파일
- [ ] Pydantic 스키마 v2.0.0 (TextSpec, VisionSpec, etc.)
- [ ] 공통 타입 정의 (BBox, Confidence, Provenance)

### Phase 2A: Stage B Enhancement (Week 2-3)
- [ ] MathpixClient 확장 (detection_map 파싱)
- [ ] content_flags, line_segments 변환
- [ ] Stage C 트리거 로직, MCP 서버 설정

### Phase 2B: Stage C Hybrid (Week 2-3)
- [ ] YOLOv8 모델 로더 및 추론
- [ ] DetectionLayer, InterpretationLayer
- [ ] HybridMerger, Fallback Strategy

### Phase 3: Testing Framework (Week 4-5)
- [ ] Golden Dataset 구조 및 50→150 샘플
- [ ] Stage별 평가 지표 (8개 Pydantic 모델)
- [ ] Smoke/Regression Test, CI 워크플로우

### Phase 4: Threshold System (Week 4-5)
- [ ] compute_effective_threshold() 3-Layer 알고리즘
- [ ] Context Modifier, FeedbackLoop
- [ ] Hard Rules, Monitoring

### Phase 5: Integration (Week 6)
- [ ] Stage D/E/G에 threshold 통합
- [ ] mathpix.md v2.0 최종 업데이트
- [ ] E2E 테스트, Canary 배포

---

## 🔑 Key Schemas (Quick Reference)

### text_spec v2.0.0 (Stage B Output)
```json
{
  "content_flags": {
    "contains_diagram": true,
    "contains_graph": true
  },
  "vision_parse_triggers": ["DIAGRAM_EXTRACTION"],
  "line_segments": [...],
  "writing_style": "printed"
}
```

### vision_spec v2.0.0 (Stage C Output)
```json
{
  "detection_layer": {"model": "yolo26-math-v1", "elements": [...]},
  "interpretation_layer": {"model": "claude-opus-4-5", "elements": [...]},
  "merged_output": {"bbox_source": "yolo26", "label_source": "claude"}
}
```

### threshold_config (요소별 base threshold)
```yaml
equation: 0.70 (CRITICAL)
curves: 0.75 (CRITICAL)
inconsistency: 0.80 (CRITICAL)
points: 0.65 (HIGH)
bbox: 0.40 (LOW)
```

---

## ⚠️ Critical Reminders

1. **Claude Vision은 bbox 생성 불가** → 반드시 YOLO 또는 Gemini 사용
2. **Mathpix API detection_map**이 Stage C 트리거의 핵심
3. **96% 설계 완성** → 남은 4%는 구현 중 해결 (training data, real API test)
4. **TodoWrite + Plan Files** = Auto-Compact 완전 복구

---

## 📖 How to Continue

```bash
# 1. 현재 진행 상태 확인
# TodoWrite가 자동으로 pending 태스크 표시

# 2. 다음 Phase 시작
/plan Phase 1: Foundation - threshold_calibration.yaml 및 Pydantic 스키마 구현

# 3. 특정 태스크 구현
# 예: [1.1] threshold_calibration.yaml 작성
```

---

> **This file is the single source of truth for project context recovery.**
> Update this file when major milestones are completed.
