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
| **E (SemanticGraph)** | `semantic_graph/builder.py` | ❌ Static | Uses `node_threshold=0.60`, `edge_threshold=0.55` |
| **G (HumanReview)** | `human_review/priority_scorer.py` | ❌ Static | Uses `critical_confidence_threshold=0.30` etc. |

---

## Tasks

| # | Phase | Task | Status | Files |
|---|-------|------|--------|-------|
| 5-1a | Stage E Threshold | Import `compute_effective_threshold`, `ThresholdConfig` | ⬜ pending | `semantic_graph/builder.py` |
| 5-1b | Stage E Threshold | Add `ThresholdConfig` to `GraphBuilderConfig` | ⬜ pending | `semantic_graph/builder.py` |
| 5-1c | Stage E Threshold | Use dynamic threshold for node/edge validation | ⬜ pending | `semantic_graph/builder.py`, `confidence.py` |
| 5-1d | Stage G Threshold | Import threshold utilities to HumanReview | ⬜ pending | `human_review/priority_scorer.py` |
| 5-1e | Stage G Threshold | Use dynamic threshold for priority scoring | ⬜ pending | `human_review/priority_scorer.py` |
| 5-2a | Documentation | Update mathpix.md Stage E section | ⬜ pending | `docs/mathpix.md` |
| 5-2b | Documentation | Update mathpix.md Stage G section | ⬜ pending | `docs/mathpix.md` |
| 5-3 | Verification | Run full E2E test suite | ⬜ pending | `tests/` |

---

## Implementation Details

### Phase 5-1a/b/c: Stage E Threshold Integration

**Current Code (builder.py:78-80):**
```python
@dataclass
class GraphBuilderConfig:
    node_threshold: float = 0.60  # Static
    edge_threshold: float = 0.55  # Static
```

**Target Code:**
```python
from ..schemas import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    compute_effective_threshold,
)

@dataclass
class GraphBuilderConfig:
    threshold_config: Optional[ThresholdConfig] = None
    threshold_context: Optional[ThresholdContext] = None

    # Fallback defaults (used when threshold_config is None)
    default_node_threshold: float = 0.60
    default_edge_threshold: float = 0.55

    def get_node_threshold(self, element_type: str, feedback: FeedbackStats) -> float:
        if self.threshold_config and self.threshold_context:
            return compute_effective_threshold(
                element_type, self.threshold_context, feedback, self.threshold_config
            )
        return self.default_node_threshold
```

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
