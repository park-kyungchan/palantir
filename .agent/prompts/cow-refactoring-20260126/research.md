# Research Report: COW Pipeline Refactoring

> Generated: 2026-01-26T15:20:00Z
> Clarify Reference: cow-refactoring-20260126
> Workload ID: cow-refactoring-20260126
> Scope: cow/src/mathpix_pipeline/**

---

## L1 Summary (< 500 tokens)

### Key Findings
- **Codebase Patterns:** 15 patterns identified
- **External Resources:** 0 (internal analysis only)
- **Risk Level:** MEDIUM
- **Complexity:** COMPLEX

### Discovered Architecture

| Stage | Module | Lines | BaseStage? | Tests? |
|-------|--------|-------|------------|--------|
| A | ingestion/ | 450+ | No | test_ingestion.py (new) |
| B | clients/mathpix.py | 280 | No | test_mathpix_client.py (new) |
| C | vision/ | 600+ | VisionParseStage | test_vision_parse.py (new) |
| D | alignment/ | 500+ | No | test_alignment.py (existing) |
| E | semantic_graph/ | 800+ | SemanticGraphStage | test_builder.py (existing) |
| F | regeneration/ | 400+ | No | test_regeneration.py (new) |
| G | human_review/ | 600+ | No | test_human_review.py (new) |
| H | export/ | 500+ | No | test_export_engine.py (new) |

### Pattern Adoption Status

```
BaseStage Pattern Adoption:
  Stage E (SemanticGraph): ✅ Full adoption (semantic_graph_stage.py)
  Stage A (Ingestion):     ✅ Full adoption (ingestion_stage.py)
  Stage C (Vision):        ✅ Full adoption (vision_parse_stage.py)
  Stage B (Text Parse):    ❌ Not adopted
  Stage D (Alignment):     ❌ Not adopted
  Stage F (Regeneration):  ❌ Not adopted
  Stage G (Human Review):  ❌ Not adopted
  Stage H (Export):        ❌ Not adopted
```

### Recommendations
1. **PRIORITY:** Complete test coverage for new test files (6 files created, need population)
2. **Phase 5 Integration:** Stage E needs `compute_effective_threshold()` integration
3. **BaseStage Migration:** Remaining 5 stages (B, D, F, G, H) should migrate to BaseStage pattern

### Next Step
`/planning --research-slug cow-refactoring-20260126`

---

## L2 Detailed Analysis

### 2.1 Codebase Pattern Analysis

#### Existing Implementations

| File | Pattern | Relevance |
|------|---------|-----------|
| stages/base.py | BaseStage abstract class | HIGH |
| stages/semantic_graph_stage.py | Full BaseStage implementation | HIGH |
| stages/ingestion_stage.py | Full BaseStage implementation | HIGH |
| stages/vision_parse_stage.py | Full BaseStage implementation | HIGH |
| pipeline.py | Orchestrator pattern | HIGH |
| schemas/*.py | Dataclass schemas | MEDIUM |
| config.py | Configuration management | MEDIUM |

#### Conventions Identified

- **Naming:**
  - Stage files: `{stage_name}_stage.py`
  - Schema files: `{domain}.py` in schemas/
  - Test files: `test_{component}.py`

- **Structure:**
  - Each stage module has: `__init__.py`, core implementation, exceptions
  - Schemas centralized in `schemas/` directory
  - Tests mirror source structure

- **Error Handling:**
  - Custom exceptions per module (e.g., `IngestionError`, `GraphBuildError`)
  - Stage-level exception wrapping via `StageError` hierarchy

- **Type Annotations:**
  - Mixed: Some files use `Optional[X]`, others use `X | None`
  - Target: Python 3.10+ style (`X | None`, `list[X]`, `dict[K, V]`)

### 2.2 Integration Points

```
Pipeline Flow:
┌─────────────────────────────────────────────────────────────────────┐
│  MathpixPipeline (pipeline.py)                                      │
│                                                                     │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐             │
│  │ Stage A │ → │ Stage B │ → │ Stage C │ → │ Stage D │             │
│  │Ingestion│   │TextParse│   │VisionPar│   │Alignment│             │
│  │ ✅ New  │   │❌Legacy │   │ ✅ New  │   │❌Legacy │             │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘             │
│        ↓                                          ↓                 │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐             │
│  │ Stage H │ ← │ Stage G │ ← │ Stage F │ ← │ Stage E │             │
│  │ Export  │   │HumanRev │   │Regen    │   │SemGraph │             │
│  │❌Legacy │   │❌Legacy │   │❌Legacy │   │ ✅ New  │             │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘             │
│                                                                     │
│  ✅ New = Uses BaseStage pattern                                    │
│  ❌ Legacy = Inline in pipeline.py or non-BaseStage                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Test coverage gaps may hide regressions | HIGH | Ensure new tests pass before refactoring |
| Pipeline.py modification could break flow | HIGH | Incremental stage extraction |
| Type annotation changes may break runtime | MEDIUM | Run mypy + full test suite |
| Threshold integration may affect accuracy | HIGH | A/B testing on sample images |

### 2.4 Test Coverage Analysis

**Existing Test Files:**
```
cow/tests/
├── alignment/
│   └── test_alignment.py           ← D: EXISTS
├── semantic_graph/
│   ├── test_builder.py             ← E: EXISTS
│   ├── test_builder_threshold.py   ← E: NEW (Phase 5)
│   ├── test_confidence.py
│   ├── test_edge_inferrer.py
│   ├── test_node_extractor.py
│   └── test_validators.py
├── clients/
│   └── test_mathpix_client.py      ← B: NEW
├── ingestion/
│   └── test_ingestion.py           ← A: NEW
├── vision/
│   └── test_vision_parse.py        ← C: NEW
├── regeneration/
│   └── test_regeneration.py        ← F: NEW
├── human_review/
│   └── test_human_review.py        ← G: NEW
├── export/
│   └── test_export_engine.py       ← H: NEW
├── e2e/
│   ├── test_full_pipeline.py
│   ├── test_happy_path.py
│   └── ...
└── integration/
    ├── test_stage_integration.py
    └── test_stage_bc_integration.py
```

### 2.5 Threshold System Analysis (Phase 5)

**Current State:**
- `SemanticGraphStageConfig` has `threshold_context` and `feedback_stats` fields
- `GraphBuilderConfig` accepts these parameters
- `SemanticGraphBuilder.build()` needs to call `compute_effective_threshold()`

**Gap:**
```python
# Current (static):
node_threshold: float = 0.60  # Hardcoded default

# Target (dynamic):
effective_threshold = compute_effective_threshold(
    base_threshold=layer1_threshold,
    context=self.config.threshold_context,
    feedback=self.config.feedback_stats,
)
```

**Files Requiring Changes:**
1. `semantic_graph/builder.py` - Replace static threshold with dynamic computation
2. `human_review/priority_scorer.py` - Integrate threshold context for priority calculation

---

## L3 Full Findings

### 3.1 Complete File Analysis

#### stages/base.py (377 lines)
- **Purpose:** Abstract base class for all pipeline stages
- **Key Classes:**
  - `ValidationResult` - Validation outcome container
  - `StageMetrics` - Execution metrics
  - `StageResult[OutputT]` - Generic result wrapper
  - `BaseStage[InputT, OutputT]` - Abstract base class
- **Key Methods:**
  - `validate(input_data) -> ValidationResult`
  - `_execute_async(input_data) -> OutputT`
  - `run_async(input_data) -> StageResult[OutputT]`
  - `get_metrics(output) -> StageMetrics`

#### stages/semantic_graph_stage.py (218 lines)
- **Status:** ✅ Full BaseStage implementation
- **Config:** `SemanticGraphStageConfig`
  - `node_threshold: float = 0.60`
  - `edge_threshold: float = 0.55`
  - `threshold_context: Optional[ThresholdContext]`
  - `feedback_stats: Optional[FeedbackStats]`
- **Gap:** `to_builder_config()` passes thresholds but builder may not use dynamic computation

#### stages/ingestion_stage.py
- **Status:** ✅ Full BaseStage implementation
- Wraps ImageLoader, ImageValidator, Preprocessor

#### stages/vision_parse_stage.py
- **Status:** ✅ Full BaseStage implementation
- Wraps YOLO detector, Gemini client, hybrid merger

#### pipeline.py (1535 lines - estimated)
- **Role:** Orchestrator for all 8 stages
- **Pattern:** Mixed - some stages use new Stage classes, others are inline
- **Target:** Reduce to <800 lines by delegating to Stage classes

### 3.2 Threshold Schema Analysis

```python
# From schemas/threshold.py

@dataclass
class ThresholdContext:
    """Layer 2: Context modifiers"""
    image_quality_score: float = 1.0
    complexity_score: float = 1.0
    source_type: str = "document"

@dataclass
class FeedbackStats:
    """Layer 3: Feedback loop adjustments"""
    total_reviews: int = 0
    acceptance_rate: float = 1.0
    recent_adjustments: List[float] = field(default_factory=list)

def compute_effective_threshold(
    base_threshold: float,
    context: Optional[ThresholdContext] = None,
    feedback: Optional[FeedbackStats] = None,
) -> float:
    """Compute effective threshold using 3-layer system."""
    # Layer 1: Base threshold
    effective = base_threshold

    # Layer 2: Context modifiers
    if context:
        effective *= context.image_quality_score
        effective *= (1.0 + (1.0 - context.complexity_score) * 0.1)

    # Layer 3: Feedback adjustments
    if feedback and feedback.total_reviews > 0:
        if feedback.acceptance_rate < 0.8:
            effective *= 0.95  # Lower threshold if too strict
        elif feedback.acceptance_rate > 0.95:
            effective *= 1.05  # Raise threshold if too lenient

    return max(0.1, min(0.99, effective))
```

### 3.3 Test File Status

| File | Status | Required Tests |
|------|--------|----------------|
| test_ingestion.py | Created | ImageLoader, Validator, Preprocessor |
| test_mathpix_client.py | Created | API mock, error handling |
| test_vision_parse.py | Created | YOLO mock, Gemini mock, merger |
| test_regeneration.py | Created | LaTeX gen, SVG gen, delta compare |
| test_human_review.py | Created | Queue mgmt, priority scorer |
| test_export_engine.py | Created | Multi-format export |
| test_builder_threshold.py | Created | Dynamic threshold integration |

### 3.4 Implementation Notes

#### BaseStage Migration Priority

1. **High Priority (Complex, Frequently Modified):**
   - Stage D (Alignment) - Complex matching logic
   - Stage F (Regeneration) - Multiple output formats

2. **Medium Priority:**
   - Stage B (Text Parse) - External API dependency
   - Stage G (Human Review) - UI integration

3. **Lower Priority:**
   - Stage H (Export) - Already well-structured

#### Test Strategy

```bash
# Recommended test execution order:
pytest cow/tests/ingestion/          # Stage A
pytest cow/tests/clients/            # Stage B
pytest cow/tests/vision/             # Stage C
pytest cow/tests/alignment/          # Stage D
pytest cow/tests/semantic_graph/     # Stage E
pytest cow/tests/regeneration/       # Stage F
pytest cow/tests/human_review/       # Stage G
pytest cow/tests/export/             # Stage H
pytest cow/tests/integration/        # Cross-stage
pytest cow/tests/e2e/                # Full pipeline
```

---

## Metadata

```yaml
research_id: cow-refactoring-20260126
workload_id: cow-refactoring-20260126
scope: cow/src/mathpix_pipeline/**
analysis_type: codebase_pattern
external_resources: false
files_analyzed: 89
patterns_identified: 15
risk_level: MEDIUM
complexity: COMPLEX
next_action: /planning --research-slug cow-refactoring-20260126
```
