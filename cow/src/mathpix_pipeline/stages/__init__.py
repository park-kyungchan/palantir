"""
Pipeline Stages Module.

Provides modular stage implementations for the COW pipeline.
Each stage follows the BaseStage interface for consistent lifecycle management.

Stage Hierarchy:
    A. IngestionStage → B. TextParseStage → C. VisionParseStage → D. AlignmentStage
                                                                         ↓
    H. ExportStage ← G. HumanReviewStage ← F. RegenerationStage ← E. SemanticGraphStage

Implemented Stages (v1.6.0):
    - Stage A: IngestionStage (image loading, validation, preprocessing)
    - Stage B: TextParseStage (Mathpix API text extraction)
    - Stage C: VisionParseStage (YOLO + Claude hybrid with fallback chain)
    - Stage D: AlignmentStage (text-vision alignment with dynamic thresholds)
    - Stage E: SemanticGraphStage (graph building with dynamic thresholds)
    - Stage F: RegenerationStage (LaTeX/SVG regeneration from semantic graph)
    - Stage G: HumanReviewStage (human review with dynamic threshold integration)
    - Stage H: ExportStage (multi-format export with parallel execution)

Module Version: 1.6.0
"""

from .base import (
    BaseStage,
    StageResult,
    StageMetrics,
    ValidationResult,
    StageError,
    StageValidationError,
    StageExecutionError,
)
from .ingestion_stage import IngestionStage, IngestionStageConfig
from .text_parse_stage import TextParseStage, TextParseStageConfig
from .alignment_stage import (
    AlignmentStage,
    AlignmentStageConfig,
    AlignmentInput,
    create_alignment_stage,
    create_alignment_input,
)
from .semantic_graph_stage import SemanticGraphStage, SemanticGraphStageConfig
from .vision_parse_stage import VisionParseStage, VisionParseStageConfig
from .regeneration_stage import RegenerationStage, RegenerationStageConfig
from .human_review_stage import (
    HumanReviewStage,
    HumanReviewStageConfig,
    HumanReviewInput,
    ReviewSummary,
    create_human_review_stage,
    create_human_review_input,
)
from .export_stage import ExportStage, ExportStageConfig, create_export_stage

__all__ = [
    # Base classes
    "BaseStage",
    "StageResult",
    "StageMetrics",
    "ValidationResult",
    # Exceptions
    "StageError",
    "StageValidationError",
    "StageExecutionError",
    # Stage implementations
    "IngestionStage",
    "IngestionStageConfig",
    "TextParseStage",
    "TextParseStageConfig",
    "VisionParseStage",
    "VisionParseStageConfig",
    "AlignmentStage",
    "AlignmentStageConfig",
    "AlignmentInput",
    "create_alignment_stage",
    "create_alignment_input",
    "SemanticGraphStage",
    "SemanticGraphStageConfig",
    "RegenerationStage",
    "RegenerationStageConfig",
    # Stage G
    "HumanReviewStage",
    "HumanReviewStageConfig",
    "HumanReviewInput",
    "ReviewSummary",
    "create_human_review_stage",
    "create_human_review_input",
    # Stage H
    "ExportStage",
    "ExportStageConfig",
    "create_export_stage",
]
