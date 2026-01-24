# Integration Execution Plan: Math Image Parsing Pipeline v2.0

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction
> **Overall Completeness:** 92%

---

## Overview

| Item | Value |
|------|-------|
| Templates Integrated | 4 |
| Total Duration | 6 weeks |
| Critical Path | T4 → (T1 ∥ T2) → T3 → mathpix.md |
| Design Completeness | 92% |

## Template Summary

| Template | Focus | Key Deliverable | Status |
|----------|-------|-----------------|--------|
| T1: Claude Vision Alt | Stage C Redesign | YOLO + Claude Hybrid | COMPLETED |
| T2: Mathpix API | Stage B Enhancement | content_flags, detection_map | COMPLETED |
| T3: Test Framework | Quality Assurance | Golden Dataset, CI/CD | COMPLETED |
| T4: Threshold Cal | Review Optimization | Dynamic thresholds | COMPLETED |

## Dependency Graph

```
Template 4 (Threshold - Foundation)
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Template 3 (Test Framework)                 │
└──────────────────────────────────────────────────────────┘
       │                              │
       ▼                              ▼
┌─────────────────────┐    ┌─────────────────────┐
│ Template 1          │    │ Template 2          │
│ Stage C: YOLO+Claude│    │ Stage B: Mathpix    │
└─────────────────────┘    └─────────────────────┘
       │                              │
       └──────────────┬───────────────┘
                      ▼
            ┌─────────────────────┐
            │  mathpix.md v2.0    │
            └─────────────────────┘
```

## mathpix.md Modification Map

### Section-by-Section Changes

| Section | Lines | Change Type | Source |
|---------|-------|-------------|--------|
| 3.B Text Parse | 149-200 | MAJOR REWRITE | T2 |
| 3.C Vision Parse | 203-262 | MAJOR REWRITE | T1 |
| 3.D Alignment | 275-328 | UPDATE | T4 |
| 3.E Semantic Graph | 332-398 | UPDATE | T4 |
| 4. JSON Schemas | 547-771 | ADD NEW | T1, T2 |
| 5. Human Review | 956-1112 | UPDATE | T4 |
| **NEW: 7. Test Strategy** | - | ADD | T3 |
| **NEW: 8. Threshold Config** | - | ADD | T4 |
| **NEW: 9. YOLO Training Spec** | - | ADD | T1 |

### Key Schema Changes

**Stage B - text_spec v2.0.0:**
```json
{
  "content_flags": {
    "contains_diagram": true,
    "contains_graph": true,
    "contains_geometry": true
  },
  "vision_parse_triggers": ["DIAGRAM_EXTRACTION"],
  "line_segments": [...],
  "writing_style": "printed"
}
```

**Stage C - Hybrid v2.0.0:**
```json
{
  "detection_layer": {"model": "yolo26-math-v1", "elements": [...]},
  "interpretation_layer": {"model": "claude-opus-4-5", "elements": [...]},
  "merged_output": {"bbox_source": "yolo26", "label_source": "claude"}
}
```

## Implementation Timeline

| Phase | Week | Focus | Deliverables |
|-------|------|-------|--------------|
| **1** | 1 | Foundation | T4 threshold config, Pydantic schemas |
| **2A** | 2-3 | Stage B | Mathpix integration, content_flags |
| **2B** | 2-3 | Stage C | YOLO pipeline, hybrid merger |
| **3** | 4-5 | Testing | Golden Dataset (150), CI/CD |
| **4** | 6 | Integration | mathpix.md v2.0, E2E test |

## Stage Confidence Scores

| Stage | Design | Implementation | Risk |
|-------|--------|----------------|------|
| A. Ingestion | 95% | HIGH | LOW |
| B. TextParse | 90% | HIGH | MEDIUM |
| C. VisionParse | 75% | MEDIUM | **HIGH** |
| D. Alignment | 95% | HIGH | LOW |
| E. SemanticGraph | 90% | HIGH | LOW |
| F. Regeneration | 100% | HIGH | LOW |
| G. HumanReview | 95% | HIGH | LOW |
| H. Export | 100% | HIGH | LOW |

## Critical Gaps (for 95%+)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| YOLO training data (1750 samples) | Stage C accuracy | 4 weeks | HIGH |
| Golden Dataset annotation (200+) | Test accuracy | 3 weeks | HIGH |
| MCP server config finalization | Stage B | 1 week | MEDIUM |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| YOLO training fails | Gemini 2.5 zero-shot fallback |
| Mathpix API changes | Abstract API layer |
| Threshold drift | Weekly monitoring + auto-adjust |
| Test data insufficient | Phased expansion (50→150→250) |

## Quick Resume After Auto-Compact

If context is compacted, resume by:
1. Read all plan files in order:
   - `.agent/plans/template_1_claude_vision_alternative.md`
   - `.agent/plans/template_2_mathpix_api_integration.md`
   - `.agent/plans/template_3_test_framework_design.md`
   - `.agent/plans/template_4_confidence_threshold_calibration.md`
   - `.agent/plans/integration_execution_plan.md` (this file)
2. Check `/home/palantir/cow/docs/mathpix.md` for current state
3. Implementation phase: Start with Phase 1 (threshold config)

## Agent Registry

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Template 1 Analysis | a90de04 | completed | No |
| Template 2 Analysis | a7b9c86 | completed | No |
| Template 3 Analysis | adedc2a | completed | No |
| Template 4 Analysis | a924480 | completed | No |
| Integration Plan | ab8ae73 | completed | No |

## Completeness Summary

```
┌─────────────────────────────────────────────┐
│  DESIGN PHASE COMPLETENESS: 92%             │
├─────────────────────────────────────────────┤
│  ✓ Stage Schemas (v2.0.0)        95%       │
│  ✓ Test Framework Design         85%       │
│  ✓ Threshold Configuration       95%       │
│  ✓ Integration Plan              90%       │
├─────────────────────────────────────────────┤
│  READY FOR: /plan code implementation      │
└─────────────────────────────────────────────┘
```

## Next Steps

1. **Immediate**: mathpix.md v2.0 작성 (이 계획 기반)
2. **Phase 1 Start**: Threshold config 구현
3. **Parallel Prep**: YOLO training data 수집 시작
4. **Code Implementation**: `/plan` 실행으로 상세 구현 계획

---

> **This plan file is the master reference for the entire design enhancement project.**
> All templates are now integrated and ready for implementation.
