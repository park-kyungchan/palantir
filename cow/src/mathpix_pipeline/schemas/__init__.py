"""
Math Image Parsing Pipeline v2.0 - Pydantic Schemas

This package contains all data schemas for the 8-stage pipeline:
- Stage A: Ingestion (external)
- Stage B: Text Parse → TextSpec
- Stage C: Vision Parse → VisionSpec
- Stage D: Alignment → AlignmentReport
- Stage E: Semantic Graph → SemanticGraph
- Stage F: Regeneration (uses SemanticGraph)
- Stage G: Human Review (uses all schemas)
- Stage H: Export (external)

Schema Version: 2.0.0
"""

# Common types (foundation for all schemas)
from .common import (
    # Enums
    WritingStyle,
    RiskLevel,
    ReviewSeverity,
    BBoxFormat,
    PipelineStage,
    # Base
    MathpixBaseModel,
    # BBox types
    BBox,
    BBoxNormalized,
    BBoxYOLO,
    # Confidence
    Confidence,
    CombinedConfidence,
    # Provenance & Review
    Provenance,
    ReviewMetadata,
    # Utilities
    utc_now,
)

# Stage A: Ingestion
from .ingestion import (
    ImageMetadata,
    ValidationResult as IngestionValidationResult,
    Region as IngestionRegion,
    IngestionSpec,
    create_ingestion_spec,
)

# Threshold configuration
from .threshold import (
    # Enums
    ComplexityLevel,
    HardRuleAction,
    # Config models
    GlobalSettings,
    FeedbackTargets,
    ElementThreshold,
    ContextModifiers,
    FeedbackLoop,
    HardRule,
    MonitoringConfig,
    CalibrationSchedule,
    ThresholdConfig,
    # Runtime models
    ThresholdContext,
    FeedbackStats,
    # Functions
    compute_effective_threshold,
)

# Stage B: Text Parse
from .text_spec import (
    # Enums
    VisionParseTrigger,
    ContentType,
    # Models
    ContentFlags,
    DetectionMapEntry,
    LineSegment,
    EquationElement,
    TableCell,
    TableElement,
    ChemicalFormula,
    WordElement,
    TextSpec,
    # Functions
    create_text_spec_from_mathpix,
)

# Stage C: Vision Parse
from .vision_spec import (
    # Enums
    DiagramType,
    ElementClass,
    RelationType,
    # Detection Layer
    DetectionElement,
    DetectionLayer,
    # Interpretation Layer
    InterpretedElement,
    InterpretedRelation,
    InterpretationLayer,
    # Merged Output
    MergedElement,
    MergedOutput,
    # Main Schema
    VisionSpec,
    # Functions
    calculate_combined_confidence,
)

# Stage D: Alignment
from .alignment import (
    # Enums
    MatchType,
    InconsistencyType,
    # Models
    TextElement,
    VisualElement,
    MatchedPair,
    Inconsistency,
    UnmatchedElement,
    AlignmentStatistics,
    AlignmentReport,
)

# Stage E: Semantic Graph
from .semantic_graph import (
    # Enums
    NodeType,
    EdgeType,
    # Models
    NodeProperties,
    SemanticNode,
    SemanticEdge,
    GraphStatistics,
    SemanticGraph,
)

# Stage G: Human Review
from .human_review import (
    # Enums
    ReviewStatus,
    ReviewDecision,
    ReviewPriority,
    CorrectionType,
    # Models
    Correction,
    Annotation,
    ReviewTaskContext,
    ReviewTask,
    ReviewResult,
    ReviewStatistics,
)

# Pipeline Orchestration
from .pipeline import (
    PipelineOptions,
    StageTiming,
    PipelineResult,
)

# Version
__version__ = "2.0.0"

__all__ = [
    # Version
    "__version__",

    # === Common ===
    "WritingStyle",
    "RiskLevel",
    "ReviewSeverity",
    "BBoxFormat",
    "PipelineStage",
    "MathpixBaseModel",
    "BBox",
    "BBoxNormalized",
    "BBoxYOLO",
    "Confidence",
    "CombinedConfidence",
    "Provenance",
    "ReviewMetadata",
    "utc_now",

    # === Stage A: Ingestion ===
    "ImageMetadata",
    "IngestionValidationResult",
    "IngestionRegion",
    "IngestionSpec",
    "create_ingestion_spec",

    # === Threshold ===
    "ComplexityLevel",
    "HardRuleAction",
    "GlobalSettings",
    "FeedbackTargets",
    "ElementThreshold",
    "ContextModifiers",
    "FeedbackLoop",
    "HardRule",
    "MonitoringConfig",
    "CalibrationSchedule",
    "ThresholdConfig",
    "ThresholdContext",
    "FeedbackStats",
    "compute_effective_threshold",

    # === Stage B: TextSpec ===
    "VisionParseTrigger",
    "ContentType",
    "ContentFlags",
    "DetectionMapEntry",
    "LineSegment",
    "EquationElement",
    "TableCell",
    "TableElement",
    "ChemicalFormula",
    "WordElement",
    "TextSpec",
    "create_text_spec_from_mathpix",

    # === Stage C: VisionSpec ===
    "DiagramType",
    "ElementClass",
    "RelationType",
    "DetectionElement",
    "DetectionLayer",
    "InterpretedElement",
    "InterpretedRelation",
    "InterpretationLayer",
    "MergedElement",
    "MergedOutput",
    "VisionSpec",
    "calculate_combined_confidence",

    # === Stage D: Alignment ===
    "MatchType",
    "InconsistencyType",
    "TextElement",
    "VisualElement",
    "MatchedPair",
    "Inconsistency",
    "UnmatchedElement",
    "AlignmentStatistics",
    "AlignmentReport",

    # === Stage E: SemanticGraph ===
    "NodeType",
    "EdgeType",
    "NodeProperties",
    "SemanticNode",
    "SemanticEdge",
    "GraphStatistics",
    "SemanticGraph",

    # === Stage G: HumanReview ===
    "ReviewStatus",
    "ReviewDecision",
    "ReviewPriority",
    "CorrectionType",
    "Correction",
    "Annotation",
    "ReviewTaskContext",
    "ReviewTask",
    "ReviewResult",
    "ReviewStatistics",

    # === Pipeline Orchestration ===
    "PipelineOptions",
    "StageTiming",
    "PipelineResult",
]
