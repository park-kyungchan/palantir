# Phase 5: Integration (Week 6)

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | **medium** |
| Total Tasks | 3 major tasks, 8 subtasks |
| Files Affected | ~6 files |
| Estimated Time | 2-3 hours |

---

## Current State Analysis

### Threshold Integration Status

| Stage | Module | Status | Details |
|-------|--------|--------|---------|
| **D (Alignment)** | `alignment/engine.py` | ✅ Done | Uses `compute_effective_threshold()` at line 228 |
| **E (SemanticGraph)** | `semantic_graph/builder.py` | ✅ Done | v2.0.0: Dynamic thresholds via `_apply_dynamic_thresholds()` at line 453 |
| **G (HumanReview)** | `human_review/priority_scorer.py` | ❌ Static | Uses `critical_confidence_threshold=0.30` etc. |

---

## Tasks

| # | Phase | Task | Status | Files |
|---|-------|------|--------|-------|
| 5-1a | Stage E Threshold | Import `compute_effective_threshold`, `ThresholdConfig` | ✅ done | `semantic_graph/builder.py:29-34` |
| 5-1b | Stage E Threshold | Add `ThresholdConfig` to `GraphBuilderConfig` | ✅ done | `semantic_graph/builder.py:94-157` |
| 5-1c | Stage E Threshold | Use dynamic threshold for node/edge validation | ✅ done | `semantic_graph/builder.py:453-536` |
| 5-1d | Stage G Threshold | Import threshold utilities to HumanReview | ⬜ pending | `human_review/priority_scorer.py` |
| 5-1e | Stage G Threshold | Use dynamic threshold for priority scoring | ⬜ pending | `human_review/priority_scorer.py` |
| 5-2a | Documentation | Update mathpix.md Stage E section | ⬜ pending | `docs/mathpix.md` |
| 5-2b | Documentation | Update mathpix.md Stage G section | ⬜ pending | `docs/mathpix.md` |
| 5-3 | Verification | Add test coverage for dynamic thresholds | ⬜ pending | `tests/semantic_graph/test_builder_threshold.py` |

---

## Implementation Details

### Phase 5-1a/b/c: Stage E Threshold Integration ✅ COMPLETE

**Status:** Implemented in v2.0.0 of `semantic_graph/builder.py`

**Implementation Summary:**
- **Lines 29-34**: Imported `ThresholdConfig`, `ThresholdContext`, `FeedbackStats`, `compute_effective_threshold`
- **Lines 94-157**: Enhanced `GraphBuilderConfig` with:
  - `threshold_config: Optional[ThresholdConfig]`
  - `threshold_context: Optional[ThresholdContext]`
  - `feedback_stats: Optional[FeedbackStats]`
  - `get_effective_node_threshold(element_type)` method
  - `get_effective_edge_threshold(edge_type)` method
- **Lines 453-536**: Implemented `_apply_dynamic_thresholds()` method:
  - Maps 28 node types to element types (points, curves, shapes, labels, equations, axes)
  - Maps 13 edge types to element types
  - Applies per-element dynamic thresholds using `compute_effective_threshold()`
  - Updates `node.applied_threshold` and `edge.applied_threshold` fields
- **Lines 414-416**: Integrated into main `build()` pipeline
- **Lines 626-628**: Integrated into `build_from_components()` alternative entry point

**Backward Compatibility:**
- Static fallback thresholds preserved: `node_threshold=0.60`, `edge_threshold=0.55`
- Used when `threshold_config` is `None`

### Phase 5-1d/e: Stage G Threshold Integration

**Current Code (priority_scorer.py:38-40):**
```python
critical_confidence_threshold: float = 0.30
high_confidence_threshold: float = 0.45
medium_confidence_threshold: float = 0.55
```

**Target Approach:**
- Add `ThresholdConfig` parameter to `PriorityScorerConfig`
- Map priority levels to element types
- Use dynamic thresholds to determine review urgency

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/phase_5_integration.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Key files:
   - `src/mathpix_pipeline/semantic_graph/builder.py`
   - `src/mathpix_pipeline/human_review/priority_scorer.py`
   - `docs/mathpix.md`

---

## Critical File Paths

```yaml
threshold_system:
  - src/mathpix_pipeline/schemas/threshold.py  # compute_effective_threshold()

stage_e:
  - src/mathpix_pipeline/semantic_graph/builder.py
  - src/mathpix_pipeline/semantic_graph/confidence.py

stage_g:
  - src/mathpix_pipeline/human_review/priority_scorer.py
  - src/mathpix_pipeline/human_review/models/task.py

documentation:
  - docs/mathpix.md

tests:
  - tests/integration/test_stage_integration.py
  - tests/e2e/test_full_pipeline.py
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing tests | HIGH | Run tests after each sub-task |
| API compatibility | MEDIUM | Keep static defaults as fallback |
| Performance overhead | LOW | `compute_effective_threshold` is O(1) |

---

## Success Criteria

- [ ] All 27 integration tests pass
- [ ] All 19 E2E tests pass
- [ ] Stage E uses dynamic threshold for node/edge confidence
- [ ] Stage G uses dynamic threshold for priority scoring
- [ ] mathpix.md reflects v2.0.0 architecture
