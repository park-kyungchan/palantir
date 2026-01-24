# Plan 3: Pipeline Completeness Verification

> **Version:** 1.0 | **Status:** READY | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction
> **Execute:** `/execute plan_3_pipeline_completeness.md`
> **Prerequisite:** Plans 1-2 completed

---

## Overview

| Item | Value |
|------|-------|
| Complexity | small |
| Total Tasks | 5 |
| Files Affected | 6 |
| Estimated Time | 1-2 hours |

---

## Current Implementation Audit

### Stage Implementation Status

| Stage | Module | Core Files | Status |
|-------|--------|------------|--------|
| A: Ingestion | `ingestion/` | `loader.py`, `validator.py`, `preprocessor.py` | ✅ Complete |
| B: TextParse | `clients/` | `mathpix.py` | ⚠️ Needs pipeline integration |
| C: VisionParse | `vision/` | `yolo_detector.py`, `gemini_client.py`, `hybrid_merger.py` | ⚠️ Needs pipeline integration |
| D: Alignment | `alignment/` | `engine.py`, `matcher.py`, `consistency.py` | ✅ Complete |
| E: SemanticGraph | `semantic_graph/` | `builder.py`, `node_extractor.py`, `edge_inferrer.py` | ✅ Complete |
| F: Regeneration | `regeneration/` | `engine.py`, `latex_generator.py`, `svg_generator.py` | ✅ Complete |
| G: HumanReview | `human_review/` | `priority_scorer.py`, `queue_manager.py` | ✅ Complete |
| H: Export | `export/` | `engine.py`, `exporters/*.py` | ✅ Complete |

### Identified Gaps

1. **Stage B/C placeholder methods** in `pipeline.py` (addressed in Plan 1)
2. **Missing `__init__.py` exports** - some modules not properly exported
3. **Schema validation** at stage boundaries
4. **Logging consistency** across stages

---

## Tasks

| # | Phase | Task | Status | File |
|---|-------|------|--------|------|
| 1 | Audit | Verify all `__init__.py` exports | pending | `*/\_\_init\_\_.py` |
| 2 | Validation | Add stage boundary validation | pending | `pipeline.py` |
| 3 | Logging | Standardize logging across stages | pending | Multiple |
| 4 | Config | Create unified configuration loader | pending | `config.py` |
| 5 | Docs | Update API documentation | pending | `docs/api/` |

---

## Implementation Details

### Task 1: Verify `__init__.py` Exports

Check and update each module's `__init__.py`:

```python
# src/mathpix_pipeline/__init__.py - Master exports
"""MathpixPipeline: Full Math Image Parsing Pipeline."""

__version__ = "2.0.0"

from .pipeline import (
    MathpixPipeline,
    PipelineError,
    IngestionConfig,
    SemanticGraphConfig,
    create_pipeline,
)

from .schemas import (
    # Common
    PipelineStage,
    BBox,
    Confidence,
    # Stage outputs
    IngestionSpec,
    TextSpec,
    VisionSpec,
    AlignmentReport,
    SemanticGraph,
    RegenerationSpec,
    ExportFormat,
)

__all__ = [
    # Pipeline
    "MathpixPipeline",
    "PipelineError",
    "IngestionConfig",
    "SemanticGraphConfig",
    "create_pipeline",
    # Schemas
    "PipelineStage",
    "BBox",
    "Confidence",
    "IngestionSpec",
    "TextSpec",
    "VisionSpec",
    "AlignmentReport",
    "SemanticGraph",
    "RegenerationSpec",
    "ExportFormat",
    # Version
    "__version__",
]
```

**Verification script:**

```python
# scripts/verify_exports.py
"""Verify all modules export correctly."""

import importlib
import sys

MODULES_TO_CHECK = [
    "mathpix_pipeline",
    "mathpix_pipeline.schemas",
    "mathpix_pipeline.alignment",
    "mathpix_pipeline.semantic_graph",
    "mathpix_pipeline.regeneration",
    "mathpix_pipeline.human_review",
    "mathpix_pipeline.export",
    "mathpix_pipeline.clients",
    "mathpix_pipeline.vision",
]

def verify_exports():
    errors = []
    for module_name in MODULES_TO_CHECK:
        try:
            module = importlib.import_module(module_name)
            if not hasattr(module, "__all__"):
                errors.append(f"{module_name}: missing __all__")
            else:
                print(f"✓ {module_name}: {len(module.__all__)} exports")
        except ImportError as e:
            errors.append(f"{module_name}: import error - {e}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    else:
        print("\nAll modules export correctly!")

if __name__ == "__main__":
    verify_exports()
```

### Task 2: Stage Boundary Validation

Add validation between stages:

```python
# src/mathpix_pipeline/pipeline.py - Add validation method

def _validate_stage_transition(
    self,
    from_stage: PipelineStage,
    to_stage: PipelineStage,
    input_data: Any,
    result: PipelineResult,
) -> bool:
    """Validate data before stage transition.

    Ensures output from one stage is valid input for next stage.

    Args:
        from_stage: Stage that produced the data
        to_stage: Stage that will consume the data
        input_data: Data to validate
        result: PipelineResult to add warnings

    Returns:
        True if validation passes
    """
    validators = {
        (PipelineStage.INGESTION, PipelineStage.TEXT_PARSE): self._validate_ingestion_to_text,
        (PipelineStage.INGESTION, PipelineStage.VISION_PARSE): self._validate_ingestion_to_vision,
        (PipelineStage.TEXT_PARSE, PipelineStage.ALIGNMENT): self._validate_text_to_alignment,
        (PipelineStage.VISION_PARSE, PipelineStage.ALIGNMENT): self._validate_vision_to_alignment,
        (PipelineStage.ALIGNMENT, PipelineStage.SEMANTIC_GRAPH): self._validate_alignment_to_graph,
        (PipelineStage.SEMANTIC_GRAPH, PipelineStage.REGENERATION): self._validate_graph_to_regen,
    }

    validator = validators.get((from_stage, to_stage))
    if validator:
        try:
            is_valid, warnings = validator(input_data)
            for warning in warnings:
                result.add_warning(warning, to_stage)
            return is_valid
        except Exception as e:
            result.add_warning(f"Validation error: {e}", to_stage)
            return True  # Continue on validation errors

    return True  # No validator = pass

def _validate_ingestion_to_text(self, spec: IngestionSpec) -> Tuple[bool, List[str]]:
    """Validate IngestionSpec for TextParse."""
    warnings = []
    if not spec.image_id:
        return False, ["Missing image_id"]
    if spec.validation and not spec.validation.is_valid:
        warnings.append("Image validation had warnings")
    return True, warnings

def _validate_text_to_alignment(self, spec: TextSpec) -> Tuple[bool, List[str]]:
    """Validate TextSpec for Alignment."""
    warnings = []
    if not spec.equations and not spec.line_segments:
        warnings.append("TextSpec has no equations or line segments")
    return True, warnings

def _validate_vision_to_alignment(self, spec: VisionSpec) -> Tuple[bool, List[str]]:
    """Validate VisionSpec for Alignment."""
    warnings = []
    if not spec.merged_output.elements:
        warnings.append("VisionSpec has no detected elements")
    return True, warnings

def _validate_alignment_to_graph(self, report: AlignmentReport) -> Tuple[bool, List[str]]:
    """Validate AlignmentReport for SemanticGraph."""
    warnings = []
    if not report.matched_pairs:
        warnings.append("No matched pairs for graph building")
    if report.overall_alignment_score < 0.3:
        warnings.append(f"Low alignment score: {report.overall_alignment_score:.2f}")
    return True, warnings

def _validate_graph_to_regen(self, graph: SemanticGraph) -> Tuple[bool, List[str]]:
    """Validate SemanticGraph for Regeneration."""
    warnings = []
    if not graph.nodes:
        warnings.append("Empty semantic graph")
    if graph.metadata.overall_confidence < 0.5:
        warnings.append(f"Low graph confidence: {graph.metadata.overall_confidence:.2f}")
    return True, warnings
```

### Task 3: Standardize Logging

Create centralized logging configuration:

```python
# src/mathpix_pipeline/logging_config.py
"""Centralized logging configuration for pipeline."""

import logging
import sys
from typing import Optional

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def configure_logging(
    level: str = "INFO",
    use_structlog: bool = True,
    json_output: bool = False,
) -> None:
    """Configure logging for the pipeline.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        use_structlog: Use structlog if available
        json_output: Output logs as JSON (for production)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if STRUCTLOG_AVAILABLE and use_structlog:
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
        ]

        if json_output:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer(colors=True))

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Standard logging fallback
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    # Set pipeline logger level
    logging.getLogger("mathpix_pipeline").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    return logging.getLogger(name)
```

### Task 4: Unified Configuration Loader

```python
# src/mathpix_pipeline/config.py
"""Unified configuration management for pipeline."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import yaml


@dataclass
class PipelineConfig:
    """Complete pipeline configuration.

    Consolidates all stage configurations into a single object.
    Can be loaded from file or environment variables.
    """
    # API Keys (from environment)
    mathpix_app_id: Optional[str] = field(default=None)
    mathpix_app_key: Optional[str] = field(default=None)
    anthropic_api_key: Optional[str] = field(default=None)

    # Stage A: Ingestion
    enable_preprocessing: bool = True
    preprocessing_operations: List[str] = field(default_factory=lambda: ["normalize", "denoise"])
    storage_enabled: bool = True
    cache_dir: Optional[str] = None

    # Stage D: Alignment
    base_alignment_threshold: float = 0.60
    base_inconsistency_threshold: float = 0.80
    enable_threshold_adjustment: bool = True

    # Stage E: Semantic Graph
    node_threshold: float = 0.60
    edge_threshold: float = 0.55
    strict_validation: bool = False

    # Stage F: Regeneration
    enable_latex_regeneration: bool = True
    enable_svg_regeneration: bool = True

    # Stage G: Human Review
    enable_human_review: bool = False
    review_threshold: float = 0.70

    # Stage H: Export
    default_export_formats: List[str] = field(default_factory=lambda: ["json"])

    # Logging
    log_level: str = "INFO"
    use_structlog: bool = True
    json_logs: bool = False

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load configuration from environment variables."""
        return cls(
            mathpix_app_id=os.getenv("MATHPIX_APP_ID"),
            mathpix_app_key=os.getenv("MATHPIX_APP_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            log_level=os.getenv("PIPELINE_LOG_LEVEL", "INFO"),
        )

    @classmethod
    def from_file(cls, path: Path) -> "PipelineConfig":
        """Load configuration from YAML or JSON file."""
        path = Path(path)
        content = path.read_text()

        if path.suffix in (".yml", ".yaml"):
            data = yaml.safe_load(content)
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings."""
        warnings = []

        if not self.mathpix_app_id or not self.mathpix_app_key:
            warnings.append("Mathpix API credentials not configured")

        if not self.anthropic_api_key:
            warnings.append("Anthropic API key not configured")

        if self.base_alignment_threshold > 0.9:
            warnings.append("High alignment threshold may reject valid matches")

        return warnings
```

### Task 5: Update API Documentation

Create `docs/api/pipeline.md`:

```markdown
# MathpixPipeline API Reference

## Quick Start

```python
from mathpix_pipeline import MathpixPipeline, PipelineOptions

# Basic usage
pipeline = MathpixPipeline()
result = await pipeline.process("path/to/image.png")

if result.success:
    print(f"Extracted: {result.semantic_graph}")
else:
    print(f"Errors: {result.errors}")
```

## Configuration

### From Environment Variables

```bash
export MATHPIX_APP_ID="your-app-id"
export MATHPIX_APP_KEY="your-app-key"
export ANTHROPIC_API_KEY="your-api-key"
```

### From Config File

```python
from mathpix_pipeline.config import PipelineConfig

config = PipelineConfig.from_file("config.yaml")
pipeline = MathpixPipeline.from_config(config)
```

### Config File Example

```yaml
# config.yaml
mathpix_app_id: ${MATHPIX_APP_ID}
mathpix_app_key: ${MATHPIX_APP_KEY}

base_alignment_threshold: 0.65
node_threshold: 0.60

enable_human_review: true
review_threshold: 0.70

default_export_formats:
  - json
  - latex

log_level: INFO
```

## Pipeline Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `skip_stages` | `List[PipelineStage]` | `[]` | Stages to skip |
| `export_formats` | `List[str]` | `["json"]` | Output formats |
| `enable_human_review` | `bool` | `False` | Enable review queue |
| `max_retries` | `int` | `3` | API retry count |

## Pipeline Result

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Overall success |
| `image_id` | `str` | Unique identifier |
| `ingestion_spec` | `IngestionSpec` | Stage A output |
| `text_spec` | `TextSpec` | Stage B output |
| `vision_spec` | `VisionSpec` | Stage C output |
| `alignment_report` | `AlignmentReport` | Stage D output |
| `semantic_graph` | `SemanticGraph` | Stage E output |
| `regeneration_spec` | `RegenerationSpec` | Stage F output |
| `export_result` | `List[ExportSpec]` | Stage H output |
| `errors` | `List[str]` | Error messages |
| `warnings` | `List[str]` | Warning messages |
| `processing_time_ms` | `float` | Total time |

## Stage Outputs

### TextSpec (Stage B)

```python
result.text_spec.equations  # List of detected equations
result.text_spec.line_segments  # Text with positions
result.text_spec.content_flags  # has_diagram, has_graph, etc.
```

### VisionSpec (Stage C)

```python
result.vision_spec.detection_layer.elements  # YOLO detections
result.vision_spec.interpretation_layer.relations  # Semantic relations
result.vision_spec.merged_output.elements  # Combined results
```

### SemanticGraph (Stage E)

```python
graph = result.semantic_graph
graph.nodes  # List[SemanticNode]
graph.edges  # List[SemanticEdge]
graph.metadata.overall_confidence  # float
```

## Error Handling

```python
from mathpix_pipeline import PipelineError
from mathpix_pipeline.clients.mathpix import MathpixError, RateLimitError

try:
    result = await pipeline.process(image)
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except MathpixError as e:
    print(f"API error: {e}")
except PipelineError as e:
    print(f"Pipeline error at {e.stage}: {e}")
```
```

---

## Verification Checklist

- [ ] All `__init__.py` files have complete `__all__`
- [ ] `verify_exports.py` script passes
- [ ] Stage boundary validation added
- [ ] Logging consistent across all stages
- [ ] Configuration loader works with env vars and files
- [ ] API documentation complete

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/plan_3_pipeline_completeness.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence

---

## Next Plan

After completing Plan 3, proceed to:
- **Plan 4:** Production Readiness (`plan_4_production_readiness.md`)
